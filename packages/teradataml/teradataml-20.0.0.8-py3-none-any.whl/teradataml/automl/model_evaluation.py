# ################################################################## 
# 
# Copyright 2025 Teradata. All rights reserved.
# TERADATA CONFIDENTIAL AND TRADE SECRET
# 
# Primary Owner: Sweta Shaw
# Email Id: Sweta.Shaw@Teradata.com
# 
# Secondary Owner: Akhil Bisht
# Email Id: AKHIL.BISHT@Teradata.com
# 
# Version: 1.1
# Function Version: 1.0
# ##################################################################

# Python libraries
import time
import ast
import warnings

# Teradata libraries
from teradataml.dataframe.dataframe import DataFrame
from teradataml.automl.model_training import _ModelTraining
from teradataml.automl.feature_exploration import _FeatureExplore
from teradataml.common.utils import UtilFuncs
from teradataml import Shap
from teradataml import TeradataMlException
from teradataml.common.logger import TeradataMlLogger, get_td_logger

@TeradataMlLogger
class _ModelEvaluator:
    
    def __init__(self, 
                 df, 
                 target_column,
                 id_column,
                 task_type,
                 cluster=False,
                 raise_errors=False):
        """
        DESCRIPTION:
            Function initializes the data, target column, features and models
            for model evaluation.
         
        PARAMETERS:  
            df:
                Required Argument.
                Specifies the model information.
                Types: teradataml Dataframe
            
            target_column:
                Required Argument.
                Specifies the target column present inside the dataset.
                Types: str
                        
            id_column:
                Required Argument.
                Specifies the id column present inside the dataset.
                Types: str
                
            task_type:
                Required Argument.
                Specifies the task type for AutoML, whether to apply regresion OR classification
                on the provived dataset.
                Permitted Values: "Regression", "Classification"
                Types: str

            cluster:
                Required Argument.
                Specifies whether to apply clustering techniques.
                Default Value: False
                Types: bool
            
            raise_errors:
                Optional Argument.
                Specifies whether to raise errors or warnings for
                non-blocking errors. When set to True, raises errors,
                otherwise raises warnings.
                Default Value: False
                Types: bool

        RETURNS:
            None

        RAISES:
            None
            
        EXAMPLES:
            >>> evaluator = _ModelEvaluator(df=model_results_df, 
            ...                             target_column="target_class",
            ...                             id_column="id", 
            ...                             task_type="Classification",
            ...                             cluster=False)

        """
        self.model_info = df
        self.target_column = target_column
        self.task_type = task_type
        self.cluster = cluster
        self.shap_results = None
        self.id_column = id_column
        self.raise_errors = raise_errors

    def model_evaluation(self, 
                         rank, 
                         table_name_mapping,
                         data_node_id, 
                         target_column_ind=True,
                         get_metrics=False,
                         is_predict=False,
                         preserve_columns=False):
        """
        DESCRIPTION:
            Function performs the model evaluation on the specified rank in leaderborad.
         
        PARAMETERS:  
            rank:
                Required Argument.
                Specifies the position of ML model for evaluation.
                Types: int
                        
            table_name_mapping:
                Required Argument.
                Specifies the mapping of train,test table names.
                Types: dict
            
            data_node_id:
                Required Argument.
                Specifies the test data node id.
                Types: str
            
            target_column_ind:
                Optional Argument.
                Specifies whether target column is present in the dataset or not.
                Default Value: True
                Types: bool
      
            get_metrics:
                Optional Argument.
                Specifies whether to return metrics or not.
                Default Value: False
                Types: bool

            is_predict:
                Optional Argument.
                Specifies whether predict is called or evaluate is called.
                Default Value: False
                Types: bool
            
            preserve_columns:
                Optional Argument.
                Specifies whether to preserve input data transformed columns in the output prediction.
                By default, "id_column", "target_column" (if present in input data), prediction and probability 
                columns are present in the output.
                Default Value: False
                Types: bool

        RETURNS:
            Predictions or performance metrics of specified rank ML model based on get_metrics parameter.

        RAISES:
            None
            
        EXAMPLES:
            >>> evaluator = _ModelEvaluator(df=model_results_df, 
            ...                             target_column="target_class", 
            ...                             task_type="Classification",
            ...                             cluster=False)
            >>> metrics_or_predictions = evaluator.model_evaluation(rank=1, 
            ...                                                     table_name_mapping={"train": "train_table", "test": "test_table"},
            ...                                                     data_node_id="test_node",
            ...                                                     target_column_ind=True,
            ...                                                     get_metrics=True,
            ...                                                     is_predict=False,
            ...                                                     preserve_columns=False)
        """
        # Setting target column indicator
        self.target_column_ind = target_column_ind
        self.table_name_mapping = table_name_mapping
        self.data_node_id = data_node_id
        self.get_metrics = get_metrics
        self.preserve_columns = preserve_columns

        # Perform evaluation
        if self.cluster:
            evaluation_results, test_data = self._evaluator(rank)
        else:
            evaluation_results = self._evaluator(rank)
        
        # Apply SHAP if applicable
        if is_predict:
            if not self.cluster:
                model_id = self.model_info.loc[rank]['MODEL_ID'].split('_')[0]
                permitted_models = ["XGBOOST", "DECISIONFOREST"]
                if model_id.upper() in permitted_models:
                    self._logger.info("Applying SHAP for Model Interpretation...")
                    self._apply_shap(rank, isload=False)
                else:
                    self._logger.info(f"SHAP is not applied for {model_id}. Only permitted models: {permitted_models}")
            else:
                self._visualize_cluster(test_data)
        return evaluation_results

    def _evaluator(self,
                   rank):
        """
        DESCRIPTION:
            Internal Function runs evaluator function for specified rank ML model
            based on regression/classification problem.
         
        PARAMETERS:  
            rank:
                Required Argument.
                Specifies the position(rank) of ML model for evaluation.
                Types: int
                
        RETURNS:
            tuple containing, performance metrics and predictions of ML model.

        RAISES:
            KeyError
            
        EXAMPLES:
            >>> metrics, prediction = self._evaluator(rank=1)     
        """
        # Extracting model using rank
        model = self.model_info.loc[rank]

        ml_name = self.model_info.loc[rank]['MODEL_ID'].split('_')[0]
        if not self.cluster:
            # Defining eval_params 
            eval_params = _ModelTraining._eval_params_generation(ml_name,
                                                                 self.target_column,
                                                                 self.task_type,
                                                                 self.id_column)

            # Extracting test data for evaluation based on data node id
            test = DataFrame(self.table_name_mapping[self.data_node_id]['{}_test'.format(model['FEATURE_SELECTION'])])

            self._logger.info("Following model is being picked for evaluation:")
            self._logger.info("Model ID : %s", model['MODEL_ID'])
            self._logger.info("Feature Selection Method : %s", model['FEATURE_SELECTION'])

            if self.task_type.lower() == 'classification':
                params = ast.literal_eval(model['PARAMETERS'])
                eval_params['output_responses'] = params['output_responses']
            
            # Mapping data according to model type
            data_map = 'test_data' if ml_name == 'KNN' else 'newdata'
            # Performing evaluation if get_metrics is True else returning predictions
            if self.get_metrics:
                metrics = model['model-obj'].evaluate(**{data_map: test}, **eval_params)
                return metrics
            else:
                # Removing target column from accumulate parameter 
                # if target column is not present in test data.
                if not self.target_column_ind:
                    eval_params.pop("accumulate", None)
                
                if self.preserve_columns:
                    # replace accumulate value to include all columns except id_column.
                    eval_params['accumulate'] = [col for col in test.columns if col != self.id_column]
                pred = model['model-obj'].predict(**{data_map: test}, **eval_params)
                return pred
        else:
            self._logger.info("Following model is being picked for evaluation of clustering:")
            self._logger.info("Model ID : %s", model['MODEL_ID'])
            self._logger.info("Feature Selection Method : %s", model['FEATURE_SELECTION'])
            feature_type = model["FEATURE_SELECTION"]
            test_table_key = f"{feature_type}_test"

            if test_table_key not in self.table_name_mapping[self.data_node_id]:
                raise KeyError(f"Table key '{test_table_key}' not found in table_name_mapping. Available keys: {self.table_name_mapping[self.data_node_id].keys()}")

            test_data = DataFrame(self.table_name_mapping[self.data_node_id][test_table_key])


            if self.get_metrics:
                from teradataml import td_sklearn as skl

                X = test_data
                result = model["model-obj"].predict(X)
                silhouette = skl.silhouette_score(X=result.select(X.columns), labels=result.select(["gridsearchcv_predict_1"]))
                calinski = skl.calinski_harabasz_score(X=result.select(X.columns), labels=result.select(["gridsearchcv_predict_1"]))
                davies = skl.davies_bouldin_score(X=result.select(X.columns), labels=result.select(["gridsearchcv_predict_1"]))

                return {
                    "SILHOUETTE": silhouette,
                    "CALINSKI": calinski,
                    "DAVIES": davies
                }, test_data
            else:
                return model["model-obj"].predict(test_data), test_data

    def _apply_shap(self, rank, isload):
        """
        DESCRIPTION:
            Applies SHAP analysis to explain model predictions after evaluation.

        PARAMETERS:
            rank:
                Required Argument.
                Specifies the position(rank) of ML model for evaluation.
                Types: int
            
            isload:
                Required Argument.
                Specifies whether load is calling the function or not.
                Types: bool

        RETURNS:
            None

        RAISES:
            None
            
        EXAMPLES:
            >>> self._apply_shap(rank=1, isload=False)
        """
        
        test_data = DataFrame(self.table_name_mapping[self.data_node_id]['{}_test'.format(self.model_info.loc[rank]['FEATURE_SELECTION'])])
        id_column = self.id_column
        input_columns = [col for col in test_data.columns if col != self.target_column and col != id_column]

        if isload:
            result_table_name = self.model_info.loc[rank, 'RESULT_TABLE']
            model_object = DataFrame(result_table_name)
        else:
            model_obj = self.model_info.loc[rank]['model-obj']
            model_object = model_obj.result
        
        # Extract model training function from MODEL_ID and format it correctly
        raw_model_id = self.model_info.loc[rank]['MODEL_ID'].split('_')[0]  # Extract base model name
        formatted_training_function = "TD_" + raw_model_id  # Add TD_ prefix
        #Currently issue with default value of model_type, it is not case insensitive
        #Hence, converting task_type to lower case
        try:
            shap_output = Shap(data=test_data,
                               object=model_object,
                               id_column=self.id_column,
                               training_function=formatted_training_function,
                               model_type=self.task_type.lower(), 
                               input_columns=input_columns,
                               detailed=True)
        except TeradataMlException as e:
            if self.raise_errors:
                raise e
            else:
                msg = f"SHAP analysis failed. Hence proceeding without SHAP analysis."
                warnings.warn(message=msg, stacklevel=2)
                return
        
        self.shap_results = shap_output.output_data
        self._logger.info("SHAP Analysis Completed. Feature Importance Available.")

        # Extract SHAP values for visualization
        df = self.shap_results
        data = next(df.itertuples())._asdict()
        
        import matplotlib.pyplot as plt
        
        # Extract keys and values
        keys = list(data.keys())
        values = list(data.values())
        
        # Plot SHAP values as a bar graph
        plt.figure(figsize=(10, 6))
        bars = plt.bar(keys, values, color='skyblue', edgecolor='black')
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, yval, f'{yval:.3f}', 
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

        plt.xticks(rotation=45, ha='right')
        plt.title('Feature Importance (SHAP Values)', fontsize=14)
        plt.xlabel('Features', fontsize=12)
        plt.ylabel('SHAP Value', fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.show()

    def _visualize_cluster(self, test_data):
        """
        DESCRIPTION:
            Visualizes clustering results for interpretability using scatter plots and centroids
            using the actual trained model and its hyperparameters.

        PARAMETERS:
            test_data:
                Required Argument.
                Specifies the test data to visualize clusters for.
                Types: teradataml DataFrame

        RETURNS:
            None

        RAISES:
            None
            
        EXAMPLES:
            >>> self._visualize_cluster(test_data=cluster_test_df)
        """
        self._logger.info("Visualizing Clusters for interpretability...")

        df = test_data.to_pandas()
        print(df.head())
        from sklearn.cluster import KMeans
        import numpy as np
        import matplotlib.pyplot as plt
        
        # Automatically pick top 2 high variance numeric features
        numerical_features = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        if self.id_column in numerical_features:
            numerical_features.remove(self.id_column)

        if len(numerical_features) < 2:
            self._logger.info("Not enough numeric features available for scatter plot.")
            return

        # Compute correlation matrix
        corr_matrix = df[numerical_features].corr()

        # Extract upper triangle without diagonal
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
        corr_vals = corr_matrix.where(mask).stack().reset_index()
        corr_vals.columns = ['Feature1', 'Feature2', 'Correlation']
        corr_vals['Abs_Correlation'] = corr_vals['Correlation'].abs()

        # Sort and select top pair
        corr_vals = corr_vals.sort_values(by='Abs_Correlation', ascending=False)
        filtered = corr_vals[corr_vals['Abs_Correlation'] > 0.1].head(1)
        variances = df[numerical_features].var().sort_values(ascending=False)
        top_features = variances.index[:2].tolist()
        self._logger.info("Selection Criteria: Top 2 High Variance Features")
        self._logger.info("Selected Features: %s, %s", top_features[0], top_features[1])
        X = df[top_features].values

        kmeans = KMeans(n_clusters=4, init='k-means++', n_init=10, max_iter=300, 
                        tol=0.0001, random_state=111, algorithm='elkan')
        kmeans.fit(X)
        
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import numpy as np
        from matplotlib.colors import ListedColormap

        # Define a fixed color map
        cmap = ListedColormap(plt.cm.Pastel2.colors)
        n_clusters = len(np.unique(kmeans.labels_))
        colors = cmap.colors[:n_clusters]

        # Plot decision regions
        h = 0.02
        x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
        y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
        xx, yy = np.meshgrid(np.arange(x_min, x_max, h),
                             np.arange(y_min, y_max, h))
        Z = kmeans.predict(np.c_[xx.ravel(), yy.ravel()])
        Z = Z.reshape(xx.shape)

        plt.figure(figsize=(14, 7))
        plt.imshow(Z, interpolation='nearest',
                   extent=(xx.min(), xx.max(), yy.min(), yy.max()),
                   cmap=ListedColormap(colors), aspect='auto', origin='lower', zorder=1)

        # Plot actual clustered data points (zorder > 1)
        cluster_colors = [colors[label] for label in kmeans.labels_]
        plt.scatter(X[:, 0], X[:, 1], c=cluster_colors, s=100, edgecolor='k', alpha=0.85, zorder=2)

        # Plot red centroids
        centroids = kmeans.cluster_centers_
        plt.scatter(centroids[:, 0], centroids[:, 1],
                    s=300, c='red', alpha=0.7, zorder=3)

        # Annotate centroids
        for i, (x, y) in enumerate(centroids):
            plt.text(x, y - 0.05, f'({x:.2f}, {y:.2f})', fontsize=9,
                    ha='center', va='top', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'), zorder=4)

        # Legend (manually matched)
        legend_handles = [mpatches.Patch(color=colors[i], label=f'Cluster {i}') for i in range(n_clusters)]
        plt.legend(handles=legend_handles, title="Cluster ID", loc='upper right')

        # Axis labels and title
        plt.xlabel(top_features[0])
        plt.ylabel(top_features[1])
        plt.title("Cluster Visualization on Test Data")
        plt.show()