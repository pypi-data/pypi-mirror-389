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
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import math
import pandas as pd
from itertools import product
import numpy as np

# Teradata libraries
from teradataml.context import context as tdmlctx
from teradataml.dataframe.copy_to import copy_to_sql
from teradataml.dataframe.dataframe import DataFrame
from teradataml import execute_sql, get_connection
from teradataml import configure, SVM, GLM, DecisionForest, XGBoost, GridSearch, KNN, RandomSearch
from teradataml.utils.validators import _Validators
from teradataml.common.utils import UtilFuncs
from teradataml.common.constants import TeradataConstants, AutoMLConstants

class _ModelTraining:
    
    def __init__(self, 
                 data, 
                 target_column,
                 id_column,
                 model_list,
                 verbose=0,
                 features=None,
                 task_type="Regression",
                 custom_data = None,
                 data_transform_dict=None,
                 **kwargs):
        """
        DESCRIPTION:
            Function initializes the data, target column, features and models
            for model training.
         
        PARAMETERS:  
            data:
                Required Argument.
                Specifies the dataset for model training phase.
                Types: teradataml Dataframe
            
            target_column:
                Required Argument. (Not required for Clustering task_type)
                Specifies the target column present inside the dataset.
                Types: str
            
            id_column:
                Required Argument.
                Specifies the name of the unique identifier column in "data".
                Types: str

            model_list:
                Required Argument.
                Specifies the list of models to be used for model training.
                Types: list
                
            verbose:
                Optional Argument.
                Specifies the detailed execution steps based on verbose level.
                Default Value: 0
                Permitted Values: 
                    * 0: prints the progress bar and leaderboard
                    * 1: prints the execution steps of AutoML.
                    * 2: prints the intermediate data between the 
                         execution of each step of AutoML.
                Types: int
                
            features:
                Required Argument.
                Specifies the list of selected feature by rfe, lasso and pca
                respectively in this order.
                Types: list of list of strings (str)
                
            task_type:
                Required Argument.
                Specifies the task type for AutoML, whether to apply regresion 
                or classification or clustering on the provived dataset.
                Default Value: "Regression"
                Permitted Values: "Regression", "Classification", "Clustering"
                Types: str
                
            custom_data:
                Optional Argument.
                Specifies json object containing user customized input.
                Types: json object
            
            data_transform_dict:
                Optional Argument.
                Specifies a dictionary containing data transformation parameters.
                Types: dict

            **kwargs:
                Specifies the additional arguments for model training. Below
                are the additional arguments:
                    volatile:
                        Optional Argument.
                        Specifies whether to put the interim results of the
                        functions in a volatile table or not. When set to
                        True, results are stored in a volatile table,
                        otherwise not.
                        Default Value: False
                        Types: bool

                    persist:
                        Optional Argument.
                        Specifies whether to persist the interim results of the
                        functions in a table or not. When set to True,
                        results are persisted in a table; otherwise,
                        results are garbage collected at the end of the
                        session.
                        Default Value: False
                        Types: bool
                    
                    seed:
                        Optional Argument.
                        Specifies the random seed for reproducibility.
                        Default Value: 42
                        Types: int
                    
                    cluster:
                        Optional Argument.
                        Specifies whether to apply clustering techniques.
                        Default Value: False
                        Types: bool
                    
                    enable_lasso:
                        Optional Argument.
                        Specifies whether to use lasso regression for feature selection.
                        By default, only RFE and PCA are used for feature selection.
                        Default Value: False
                        Types: bool

        RETURNS:
            None
        
        RAISES:
            None
            
        EXAMPLES:
            >>> rfe_features = ["feature1", "feature2", "feature3"]
            >>> lasso_features = ["feature1", "feature4", "feature5"]
            >>> pca_features = ["pc1", "pc2", "pc3"]
            >>> feature_lists = [rfe_features, lasso_features, pca_features]
            >>> model_trainer = _ModelTraining(data=scaled_df, 
            ...                                target_column="target",
            ...                                id_column="id",
            ...                                model_list=["xgboost", "randomforest"],
            ...                                verbose=1,
            ...                                features=feature_lists,
            ...                                task_type="Classification",
            ...                                persist=True,
            ...                                seed=42)
        """
        self.data = data
        self.target_column = target_column
        self.id_column = id_column
        self.model_list = model_list
        self.verbose = verbose
        self.task_type = task_type
        self.custom_data = custom_data
        self.labels = self.data.drop_duplicate(self.target_column).size
        self.startify_col = None
        self.persist = kwargs.get("persist", False)
        self.volatile = kwargs.get("volatile", False)
        self.seed = kwargs.get("seed", 42)
        self.cluster = kwargs.get("cluster", False)
        self.enable_lasso = kwargs.get("enable_lasso", False)
        
        self.data_transform_dict = data_transform_dict if data_transform_dict is not None else {}

        if not self.cluster:
            # For non-clustering: include lasso features only if lasso selection is enabled
            self.features = tuple(features[:3 if self.enable_lasso else 2])
        else:
            # For clustering: always use first two feature sets (pca and non pca)
            self.features = tuple(features[:2])

    def model_training(self, 
                       auto=True,
                       max_runtime_secs=None,
                       stopping_metric=None, 
                       stopping_tolerance=0,
                       max_models=None):
        """
        DESCRIPTION:
            Function to perform following tasks:-
                1. Generates the hyperparameters for different ML models.
                2. Performs hyperparameter tunning for different ML models in parallel.
                3. Displays the leaderboard of trained ML models.
         
        PARAMETERS:           
            auto:
                Optional Argument.
                Specifies whether to run data preparation in auto mode or custom mode.
                When set to True, runs automtically otherwise, it take user inputs.
                Default Value: True
                Types: boolean  
                
            max_runtime_secs:
                Optional Argument.
                Specifies the time limit in seconds for model training.
                Types: int
                
            stopping_metric:
                Required, when "stopping_tolerance" is set, otherwise optional.
                Specifies the stopping mertics for stopping tolerance in model training.
                Types: str

            stopping_tolerance:
                Required, when "stopping_metric" is set, otherwise optional.
                Specifies the stopping tolerance for stopping metrics in model training.
                Types: float
            
            max_models:
                Optional Argument.
                Specifies the maximum number of models to be trained.
                Types: int
     
        RETURNS:
            pandas dataframes containing model information, leaderboard,
            data transformation dictionary, and target column distinct count.

        RAISES:
            None
            
        EXAMPLES:
            >>> model_trainer = _ModelTraining(data=scaled_df, 
            ...                                target_column="target", 
            ...                                model_list=["xgboost", "randomforest"],
            ...                                features=feature_lists,
            ...                                task_type="Classification")
            >>> model_info, leaderboard, data_transformation_params, \
            ...    target_count = model_trainer.model_training(auto=True, max_models=10)
        """
        self.stopping_metric = stopping_metric
        self.stopping_tolerance = stopping_tolerance
        self.max_runtime_secs = max_runtime_secs
        self.max_models = max_models
        
        self._display_heading(phase=3, progress_bar=self.progress_bar)
        self._display_msg(msg='Model Training started ...',
                          progress_bar=self.progress_bar,
                          show_data=True)
        # Generates the hyperparameters for different ML models
        parameters = self._generate_parameter()
        
        # handles customized hyperparameters
        if not auto:
            parameters = self._custom_hyperparameters(parameters)
        
        # Validates the upper limit of max_models based on total model combinations
        if self.max_models is not None:
            self._validate_upper_limit_for_max_models(parameters)
            
        if self.verbose == 2:
            self._display_hyperparameters(parameters)

        # Parallel execution of hpt
        trained_models_info = self._parallel_training(parameters)
        
        # Displaying leaderboard
        leader_board, models = self._display_leaderboard(trained_models_info)
        
        self._display_heading(phase=4,
                              progress_bar=self.progress_bar)
        self.progress_bar.update()
            
        return models, leader_board, self.data_transform_dict, self.labels

    def _get_model_param_space(self,
                               hyperparameters):
        """
        DESCRIPTION:
            Internal function to calculate the total number of models to be trained for specific model.
        
        PARAMETERS:
            hyperparameters:
                Required Argument.
                Specifies the hyperparameters availables for ML model.
                Types: list of dict
        
        RETURNS:
            int containing, total number of models available for training.
        
        RAISES:
            None
            
        EXAMPLES:
            >>> models_count = self._get_model_param_space(hyperparameters={'name': 'xgboost', 'max_depth': (5, 7, 10)})
        """
        # Creating all possible combinations of hyperparameters
        if 'param_grid' in hyperparameters:
            grid = hyperparameters['param_grid']
        else:
            # AutoML style: full dict is hyperparameter space
            grid = hyperparameters
        all_combinations = list(product(*[v if isinstance(v, (list, tuple)) else [v] for v in grid.values()]))
        # Getting total number of models for each model model training function
        total_models = len(all_combinations)
        return total_models

    def _validate_upper_limit_for_max_models(self,
                                             hyperparameters_list):
        """
        DESCRIPTION:
            Internal function to validate the upper limit of max_models.
        
        PARAMETERS:
            hyperparameters_list:
                Required Argument.
                Specifies the hyperparameters for different ML models.
                Types: list of dict
        
        RETURNS:
            None
        
        RAISES:
            TeradataMlException, ValueError
            
        EXAMPLES:
            >>> self._validate_upper_limit_for_max_models(hyperparameters_list=[{'name': 'xgboost', 'max_depth': (5, 7)}, {'name': 'svm', 'lambda1': (0.01, 0.1)}])
        """
        model_param_space = 0
        for hyperparameter_dct in hyperparameters_list:
            # getting total number of models for each model
            total_models = self._get_model_param_space(hyperparameter_dct)
            model_param_space += total_models
            
        # Validating upper range for max_models 
        _Validators._validate_argument_range(self.max_models, "max_models", ubound=model_param_space, ubound_inclusive=True)
    
    def _display_hyperparameters(self,
                                 hyperparameters_list):
        """
        DESCRIPTION:
            Internal function to display the hyperparameters for different ML models.
         
        PARAMETERS:
            hyperparameters_list:
                Required Argument.
                Specifies the hyperparameters for different ML models.
                Types: list of dict
        
        RETURNS:
            None
        
        RAISES:
            None
            
        EXAMPLES:
            >>> self._display_hyperparameters(hyperparameters_list=[{'name': 'xgboost', 'max_depth': (5, 7)}, {'name': 'svm', 'lambda1': (0.01, 0.1)}])
        """	
        self._display_msg(msg="Hyperparameters used for model training: ",
                          progress_bar=self.progress_bar,
                          show_data=True)
        print(" " *150, end='\r', flush=True)

        # Iterating over hyperparameters_list
        for hyperparameter_dct in hyperparameters_list:
            name = hyperparameter_dct.get("name", "Unnamed Model")
            self._display_msg(msg=f"Model: {name}")

            if self.cluster and "param_grid" in hyperparameter_dct:
                # Also show metadata outside param_grid
                self._display_msg(msg=f"Hyperparameter Grid: {hyperparameter_dct['param_grid']}")    
            else:
                self._display_msg(msg=f"Hyperparameters: {hyperparameter_dct}")
            
            total_models = self._get_model_param_space(hyperparameter_dct)

            self._display_msg(msg=f"Total number of models for {name}: {total_models}")
            print(f"--" * 100 + "\n")
    
    def _display_leaderboard(self, 
                             trained_models_info):
        """
        DESCRIPTION:
            Internal function to display the trainined ML models.
         
        PARAMETERS:
            trained_models_info:
                Required Argument.
                Specifies the trained models information to display.
                Types: pandas Dataframe
        
        RETURNS:
            tuple containing, leaderboard as pandas Dataframe and sorted models as pandas Dataframe
        
        RAISES:
            None
            
        EXAMPLES:
            >>> leaderboard, sorted_model_df = self._display_leaderboard(trained_models_info=trained_models_df)
        """
        # Initialize sorted_model_df
        if trained_models_info.empty:
            self._display_msg(msg="No models were trained successfully. Please check error logs for details.",
                              progress_bar=self.progress_bar,
                              show_data=True)
            sorted_model_df = trained_models_info.copy()
        else:
            # Sort based on task type and clustering
            if not self.cluster:
                if self.task_type != "Regression":
                    sorted_model_df = trained_models_info.sort_values(by=['MICRO-F1', 'WEIGHTED-F1'], 
                                                                      ascending=[False, False]).reset_index(drop=True)
                else:
                    sorted_model_df = trained_models_info.sort_values(by='R2', 
                                                                      ascending=False).reset_index(drop=True)
            else:
                sorted_model_df = trained_models_info.sort_values(by=['SILHOUETTE', 'CALINSKI', 'DAVIES'],
                                                                  ascending=[False, False, True]).reset_index(drop=True)


        # Adding rank to leaderboard
        sorted_model_df.insert(0, 'RANK', sorted_model_df.index + 1) 

        # Internal Data list for leaderboard
        dp_lst = ["model-obj", "DATA_TABLE", "RESULT_TABLE", "PARAMETERS"]

        # Excluding the model object and model name from leaderboard
        leaderboard = sorted_model_df.drop(columns=[col for col in dp_lst if col in sorted_model_df.columns])

        # Filter rows based on max_models only for non-empty DataFrame
        if not trained_models_info.empty and self.max_models is not None:
            leaderboard = leaderboard[leaderboard["RANK"] <= self.max_models]
        
        self._display_msg(msg="Leaderboard",
                          progress_bar=self.progress_bar,
                          data=leaderboard,
                          show_data=True)
        
        return leaderboard, sorted_model_df

    def _update_hyperparameters(self,
                                existing_params, 
                                new_params):
        """
        DESCRIPTION:
            Function to update customized hyperparameters by performing addition or replacement 
            based on user input.

        PARAMETERS:  
            existing_params:
                Required Argument.
                Specifies the existing generated hyperparameters for specific model.
                Types: dict

            new_params:
                Required Argument.
                Specifies the newly passed hyperparameters from user input.
                Types: dict
                
        RETURNS:
            Updated dictionary containing hyperparameters for specific model.
        
        RAISES:
            None
            
        EXAMPLES:
            >>> params = self._update_hyperparameters(existing_params={'max_depth': (5, 7)}, new_params={'max_depth': {'Method': 'ADD', 'Value': [10, 15]}})
        """
        # Iterating over new hyperparameters and performing required operation 
        # based on passed method ADD or REPLACE
        if self.cluster:
            # Clustering: use param_grid
            param_grid = existing_params.get("param_grid", {})
            for feature, param_list in new_params.items():
                if feature in param_grid:
                    if param_list["Method"] == "ADD":
                        param_grid[feature] = list(param_grid[feature])
                        param_grid[feature].extend(param_list["Value"])
                        param_grid[feature] = tuple(set(param_grid[feature]))
                    elif param_list["Method"] == "REPLACE":
                        param_grid[feature] = tuple(param_list["Value"])
                    else:
                        self._display_msg(inline_msg="Passed method is not valid.")
                else:
                    param_grid[feature] = tuple(param_list["Value"])
            existing_params["param_grid"] = param_grid

        else:
            for feature, param_list in new_params.items():
                if feature in existing_params.keys():
                    if param_list["Method"] == "ADD":
                        # Extending existing list
                        existing_params[feature] = list(existing_params[feature])
                        existing_params[feature].extend(param_list["Value"])
                        # Updating list with unique values.
                        existing_params[feature]=tuple(set(existing_params[feature]))
                    elif param_list["Method"] == "REPLACE":
                        # Replacing with entirely new value
                        existing_params[feature] = tuple(param_list["Value"])
                    else:
                        self._display_msg(inline_msg="Passed method is not valid.")
                else:
                    self._display_msg(inline_msg="Passed model argument {} is not"
                                      " available for model {}. Skipping it."
                                      .format(feature,existing_params['name']))
                    continue
            # Returning updated hyperparamter
        return existing_params

    def _custom_hyperparameters(self,
                                hyperparameters):
        """
        DESCRIPTION:
            Function to extract and update hyperaparameters from user input for model training.

        PARAMETERS:  
            hyperparameters:
                Required Argument.
                Specifies the existing generated hyperparameters for all models.
                Types: list
                
        RETURNS:
             Updated list of dictionaries containing hyperparameterd for all models.
        
        RAISES:
            None
            
        EXAMPLES:
            >>> hyperparameters = self._custom_hyperparameters(hyperparameters=[{'name': 'xgboost', 'max_depth': (5, 7)}, {'name': 'svm', 'lambda1': (0.01, 0.1)}])
        """
        self._display_msg(msg="Starting customized hyperparameter update ...",
                          progress_bar=self.progress_bar,
                          show_data=True)
        
        # Fetching user input for performing hyperparameter tuning 
        hyperparameter_tuning_input = self.custom_data.get("HyperparameterTuningIndicator", False) 
        if hyperparameter_tuning_input:
            # Extracting models and its corresponding hyperparameters details
            model_hyperparameters = self.custom_data.get("HyperparameterTuningParam", None)
            # Getting model index for mapping
            model_index_param = self.model_mapping
            # Checking hyperparameters passed by user and mapping them according to model
            if model_hyperparameters:
                for model_name, hyp_list in model_hyperparameters.items():
                    if model_name in list(model_index_param.keys()):
                        model_index = model_index_param[model_name]
                    else:
                        self._display_msg(inline_msg="Passed model {} is not available for training.".format(model_name))
                        continue
                    # Updating existing hyperparameters with customized hyperparameters as per user input
                    hyperparameters[model_index]=self._update_hyperparameters(hyperparameters[model_index],hyp_list)
                # Displaying it after update
                self._display_msg(inline_msg="Completed customized hyperparameter update.",
                                  progress_bar=self.progress_bar)
            else:
                self._display_msg(inline_msg="No information provided for custom hyperparameters. AutoML will proceed with default values.",
                                  progress_bar=self.progress_bar)
        else:
            self._display_msg(inline_msg="Skipping customized hyperparameter tuning",
                              progress_bar=self.progress_bar)
        # Retunring updated hyperparameters for all models    
        return hyperparameters
    
    # Hyperparameter generation for XGBoost or Decision Forest
    def _get_tree_model_hyperparameters(self,
                                        num_rows, 
                                        num_cols,
                                        model_name):
        """
        DESCRIPTION:
            Internal function to generate hyperparameters for tree based model i.e., XGBoost or Decision Forest.
         
        PARAMETERS:
            num_rows:
                Required Argument.
                Specifies the number of rows in dataset.
                Types: int
                
            num_cols:
                Required Argument.
                Specifies the number of columns in dataset.
                Types: int

            model_name:
                Required Argument.
                Specifies which linear model is getting used for generating hyperparameters.
                Types: Str
                
        RETURNS:
            dict containing, hyperparameters for XGBoost or Decision Forest.
        
        RAISES:
            None
            
        EXAMPLES:
            >>> params = self._get_tree_model_hyperparameters(num_rows=5000, num_cols=15, model_name="xgboost")
        """
        # Initializing hyperparameters based on default value
        min_impurity = [0.0]
        shrinkage_factor = [0.5]
        max_depth = [5]
        min_node_size = [1]
        iter_num = [10]
        num_trees = [-1]
        lambda1 = [1.0]  # Initialize lambda1 with default value
        num_boosted_trees = [-1]  # Initialize num_boosted_trees with default value
        
        # Extending values for hyperparameters based on dataset size, i.e., number of rows and columns
        if num_rows < 1000 and num_cols < 10:
            min_impurity.extend([0.1])
            shrinkage_factor.extend([0.1, 0.2])
            max_depth.extend([6, 7, 8])
            min_node_size.extend([2])
            iter_num.extend([20])
            lambda1.extend([0.001, 0.01])
            num_boosted_trees.extend([2, 5])
        elif num_rows < 10000 and num_cols < 15:
            min_impurity.extend([0.1, 0.2])
            shrinkage_factor.extend([0.1, 0.3])
            max_depth.extend([6, 8, 10])
            min_node_size.extend([2, 3])
            iter_num.extend([20, 30])
            lambda1.extend([0.01, 0.1])
            num_boosted_trees.extend([5, 10])
        elif num_rows < 100000 and num_cols < 20:
            min_impurity.extend([0.2, 0.3])
            shrinkage_factor.extend([0.01, 0.1, 0.2])
            max_depth.extend([4, 6, 7])
            min_node_size.extend([3, 4])
            iter_num.extend([30, 40])
            lambda1.extend([0.1, 1.0])
            num_boosted_trees.extend([10, 20])
        else:
            min_impurity.extend([0.1, 0.2, 0.3])
            shrinkage_factor.extend([0.01, 0.05, 0.1])
            max_depth.extend([3, 4, 7, 8])
            min_node_size.extend([2, 3, 4])
            iter_num.extend([20, 30, 40])
            lambda1.extend([1.0, 10.0, 100.0])
            num_boosted_trees.extend([20, 50, 100])

        # Hyperparameters for XGBoost model
        xgb_params = {
                'response_column': self.target_column,
                'name':'xgboost',
                'model_type': 'Regression',
                'column_sampling': (1, .6),
                'min_impurity': tuple(min_impurity),
                'lambda1': tuple(lambda1),
                'shrinkage_factor': tuple(shrinkage_factor),
                'max_depth': tuple(max_depth),
                'min_node_size': tuple(min_node_size),
                'iter_num': tuple(iter_num),
                'num_boosted_trees': tuple(num_boosted_trees),
                'seed': self.seed
                }
        # Hyperparameters for Decision Forest model
        df_params = {
                'response_column': self.target_column, 
                'name': 'decision_forest',
                'tree_type': 'Regression',
                'min_impurity': tuple(min_impurity),
                'max_depth': tuple(max_depth),
                'min_node_size': tuple(min_node_size),
                'num_trees': tuple(num_trees),
                'seed': self.seed
        }
        
        # Updating model type in case of classification
        if self.task_type == "Classification":
            xgb_params['model_type'] = 'Classification'
            df_params['tree_type'] = 'Classification'

        # Returning hyperparameters based on passed model
        if model_name == 'xgboost':
            return xgb_params
        elif model_name == 'decision_forest':
            return df_params
        else:
            return None

    # Hyperparameter generation for KNN
    def _get_knn_hyperparameters(self,
                                 num_rows=None, 
                                 num_cols=None):
        """
        DESCRIPTION:
            Internal function to generate hyperparameters for KNN.
         
        PARAMETERS:
            num_rows
                Required Argument.
                Specifies the number of rows in dataset.
                Types: int
                
            num_cols:
                Required Argument.
                Specifies the number of columns in dataset.
                Types: int
                
        RETURNS:
            dict containing, hyperparameters for KNN.
        
        RAISES:
            None
            
        EXAMPLES:
            >>> params = self._get_knn_hyperparameters(num_rows=2000, num_cols=12)
        """
        params = {
                'response_column': self.target_column,
                'name': 'knn',
                'model_type': 'Regression',
                'k': (3, 5, 6, 8, 10, 12),
                "id_column": self.id_column,
                "voting_weight": 1.0
                }
        
        if self.task_type == "Classification":
            params['model_type'] = 'Classification'
    
        return params

    # Hyperparameter generation for SVM/GLM
    def _get_linear_model_hyperparameters(self,
                                          num_rows,
                                          num_cols,
                                          model_name):
        """
        DESCRIPTION:
            Internal function to generate hyperparameters for linear models i.e., SVM or GLM.
         
        PARAMETERS:               
            num_rows:
                Required Argument.
                Specifies the number of rows in dataset.
                Types: int
                
            num_cols:
                Required Argument.
                Specifies the number of columns in dataset.
                Types: int

            model_name:
                Required Argument.
                Specifies which tree model is getting used for generating hyperparameters.
                Types: Str
                
        RETURNS:
            dict containing, hyperparameters for SVM or GLM.
        
        RAISES:
            None
            
        EXAMPLES:
            >>> params = self._get_linear_model_hyperparameters(num_rows=10000, num_cols=25, model_name="glm")
        """
        # Initializing hyperparameters based on default value
        iter_max = [300]
        batch_size = [10]
        
        # Extending values for hyperparameters based on dataset size i.e., number of rows and columns
        if num_rows < 1000 and num_cols < 10:
            iter_max.extend([100, 200])
            batch_size.extend([20, 40, 50])
        elif num_rows < 10000 and num_cols < 15:
            iter_max.extend([200, 400])
            batch_size.extend([50, 60, 80])
        elif num_rows < 100000 and num_cols < 20:
            iter_max.extend([400])
            batch_size.extend([100, 150])
        else:
            iter_max.extend([200, 400, 500])
            batch_size.extend([80, 100, 150])
            
        # Hyperparameters for SVM model    
        svm_params = { 
                'response_column': self.target_column,
                'name':'svm', 
                'model_type':'regression',
                'lambda1':(0.001, 0.02, 0.1),
                'alpha':(.15, .85),
                'tolerance':(0.001, 0.01),
                'learning_rate':('Invtime','Adaptive','constant'),
                'initial_eta' : (0.05, 0.1),
                'momentum':(0.65, 0.8, 0.95),
                'nesterov': True,
                'intercept': True,
                'iter_num_no_change':(5, 10, 50),
                'local_sgd_iterations ': (10, 20),
                'iter_max' : tuple(iter_max),
                'batch_size' : tuple(batch_size)
                }
        # Hyperparameters for GLM model
        glm_params={
                'response_column': self.target_column,
                'name': 'glm',
                'family': 'GAUSSIAN',
                'lambda1':(0.001, 0.02, 0.1),
                'alpha': (0.15, 0.85),
                'learning_rate': ('invtime', 'constant', 'adaptive'),
                'initial_eta': (0.05, 0.1),
                'momentum': (0.65, 0.8, 0.95),
                'iter_num_no_change':(5, 10, 50),
                'iter_max' : tuple(iter_max),
                'batch_size' : tuple(batch_size)
                }
        
        # Updating model type in case of classification    
        if self.task_type == "Classification":
            svm_params['model_type'] = 'Classification'
            svm_params['learning_rate'] =  'OPTIMAL'
            glm_params['family'] = 'BINOMIAL'
            glm_params['learning_rate'] =  'OPTIMAL'
        
        # Returning hyperparameters based on passed model    
        if model_name == 'svm':
            return svm_params
        elif model_name == 'glm':
            return glm_params
        else:
            return None

    def _get_kmeans_hyperparameters(self):
        """
        DESCRIPTION:
            Generates hyperparameters for kmeans clustering.
        
        PARAMETERS:
            None
            
        RETURNS:
            dict containing hyperparameters for kmeans.
        
        RAISES:
            None
            
        EXAMPLES:
            >>> params = self._get_kmeans_hyperparameters()
        """
        params = {
            "name": "kmeans",
            "param_grid": {
                'n_clusters': (2,3,4,5,6,7,8,9,10),
                'init': ('k-means++', 'random'),
                'n_init': (5, 10),
                'max_iter': (100, 200),
                'tol': (0.001, 0.01),
                'algorithm': ('lloyd', 'elkan')
            }
        }

        return params

    def _get_gmm_hyperparameters(self):
        """
        DESCRIPTION:
            Generates hyperparameters for Gaussian Mixture Model (GMM).
        
        PARAMETERS:
            None
            
        RETURNS:
            dict containing hyperparameters for GMM.
        
        RAISES:
            None
            
        EXAMPLES:
            >>> params = self._get_gmm_hyperparameters()
        """
        params = {
            "name": "gaussianmixture",
            "param_grid": {
                "n_components": (2,3,4,5,6,7,8,9,10),
                "covariance_type": ("full", "tied", "diag", "spherical"),
                "max_iter": (100, 300)
            }
        }
        
        return params
    
    def _generate_parameter(self):
        """
        DESCRIPTION:
            Internal function to generate hyperparameters for ML models.
        
        PARAMETERS:
            None
                
        RETURNS:
            list containing, dict of hyperparameters for different ML models.
        
        RAISES:
            ValueError
            
        EXAMPLES:
            >>> parameters = self._generate_parameter()
        """
        # list for storing hyperparameters
        parameters = []
        # Index for model mapping
        model_index = 0
        # Dictionary for mapping model with index
        self.model_mapping={}
        if not self.cluster:
            # Getting number of rows and columns
            num_rows = self.data.shape[0]
            num_cols = self.data.shape[1]
              
            # Model functions mapping for hyperparameter generation           
            model_functions = {
                'decision_forest': self._get_tree_model_hyperparameters,
                'xgboost': self._get_tree_model_hyperparameters,
                'knn': self._get_knn_hyperparameters,
                'glm': self._get_linear_model_hyperparameters,
                'svm': self._get_linear_model_hyperparameters,
            }
            
            if not self.cluster:
                supported_models = AutoMLConstants.SUPERVISED_MODELS.value
                self.model_list = [model for model in self.model_list if model in supported_models]
                
            # Generating hyperparameters for each model
            if self.model_list:
                for model in self.model_list:
                    self.model_mapping[model] = model_index
                    if model == 'knn':
                        parameters.append(model_functions[model](num_rows, num_cols))
                    else:
                        parameters.append(model_functions[model](num_rows, num_cols, model))
                    model_index += 1
            else:
                raise ValueError("No model is selected for training.")
        else:
            model_functions = {
                'kmeans': self._get_kmeans_hyperparameters,
                'gaussianmixture': self._get_gmm_hyperparameters,
            }
            supported_models = AutoMLConstants.CLUSTERING_MODELS.value
            self.model_list = [model for model in self.model_list if model in supported_models]
            if self.model_list:
                for model in self.model_list:
                    self.model_mapping[model] = model_index
                    parameters.append(model_functions[model]())
                    model_index += 1
            else:
                raise ValueError("No model is selected for training.")

        return parameters
    
    def distribute_max_models(self):
        """
        DESCRIPTION:
            Internal function to distribute max_models across available model functions.
        
        PARAMETERS:
            None
        
        RETURNS:
            dictionary containing max_models distribution and list of models to remove.
        
        RAISES:
            None
            
        EXAMPLES:
            >>> model_distribution, models_to_remove = self.distribute_max_models()
        """
        if self.cluster:
            models = [model for model in self.model_list if model in AutoMLConstants.CLUSTERING_MODELS.value]
        else:
            models = [model for model in self.model_list if model in AutoMLConstants.SUPERVISED_MODELS.value]
        # Getting total number of models
        model_count = len(models)
        # Evenly distributing max_models across models
        base_assign = self.max_models // model_count
        # Creating list of max_models for each model
        distribution = [base_assign] * model_count
        
        # Calculating remaining models
        remaining_model_count = self.max_models % model_count
        if remaining_model_count:
            # distributing remaining model across models.
            # Starting from first model in list and distributing remaining models by 1 each.
            for i in range(remaining_model_count):
                distribution[i] += 1
        
        # Creating dictionary for model distribution
        model_distribution = dict(zip(models, distribution))
        # Getting list of models with 0 distribution and removing them from model list
        # While for model having distribution greater than 0, updating distribution with 
        # 1/3rd of original value as we are training with 3 different feature selection methods.
        models_to_remove = []
        # Feature selection count: cluster(2), with lasso(3), without lasso (2)
        fs_count = 2 if self.cluster else (3 if self.enable_lasso else 2)
        
        for model in models:
            initial_count = model_distribution[model]          
            if initial_count == 0:
                models_to_remove.append(model)
            else:
                model_distribution[model] = math.ceil(initial_count / fs_count)   
        
        return model_distribution, models_to_remove

    def _parallel_training(self, parameters):
        """
        DESCRIPTION:
            Internal function initiates the threadpool executor 
            for hyperparameter tunning of ML models.
         
        PARAMETERS:
             parameters:
                Required Argument.
                Specifies the hyperparamters for ML models.
                Types: list of dict

        RETURNS:
            Pandas DataFrame containing, trained models information.
        
        RAISES:
            None
            
        EXAMPLES:
            >>> models_df = self._parallel_training(parameters=[{'name': 'xgboost', 'max_depth': (5, 7)}, {'name': 'svm', 'lambda1': (0.01, 0.1)}])
        """ 
        self.model_id_counters = {}
        # Hyperparameters for each model
        model_params = parameters[:min(len(parameters), 5)]
        self._display_msg(msg="Performing hyperparameter tuning ...", progress_bar=self.progress_bar)

        # Defining training data
        if not self.cluster:
            # Include lasso data only if lasso selection is enabled
            data_types = (['lasso', 'rfe', 'pca'] if self.enable_lasso else ['rfe', 'pca'])
            training_datas = tuple(DataFrame(self.data_mapping[f'{data_type}_train']) for data_type in data_types)
        else:
            data_types = ['pca', 'non_pca']
            training_datas = tuple(DataFrame(self.data_mapping[f'{data_type}_train']) for data_type in data_types)

        if self.task_type == "Classification" and not self.cluster:
            response_values = training_datas[0].get(self.target_column).drop_duplicate().get_values().flatten().tolist()
            self.output_response = [str(i) for i in response_values]

        if self.stopping_metric is None:
            if not self.cluster:
                self.stopping_tolerance, self.stopping_metric = 1.0, 'MICRO-F1' \
                                        if self.is_classification_type() else 'R2'
            else:
                self.stopping_tolerance, self.stopping_metric = 1.0, 'SILHOUETTE'

        self.max_runtime_secs = self.max_runtime_secs/len(model_params) \
                                if self.max_runtime_secs is not None else None
                   
        if self.max_models is not None:
            # Getting model distribution and models to remove
            self.max_models_distribution, models_to_remove = self.distribute_max_models()
            # Removing model parameters with 0 distribution
            if len(models_to_remove):
                for model in models_to_remove:
                    model_params = [param for param in model_params if param['name'] != model]
                    # Updating progress bar as we are removing model
                    self.progress_bar.update()

        if self.is_classification_type() and not self.cluster:
            self.startify_col = self.target_column

        trained_models = []
        
        for param in model_params:
            result = self._hyperparameter_tunning(param, training_datas)
            if result is not None:
                trained_models.append(result)
        
        if trained_models:
            models_df = pd.concat(trained_models, ignore_index=True)
        else:
            # Create empty DataFrame with exact same columns as successful case
            if self.cluster:
                columns = AutoMLConstants.CLUSTERING_COLUMNS.value
            elif self.task_type == "Classification":
                columns = AutoMLConstants.CLASSIFICATION_COLUMNS.value
            elif self.task_type == "Regression":
                columns = AutoMLConstants.REGRESSION_COLUMNS.value

            models_df = pd.DataFrame(columns=columns)
        
        return models_df
  
    def _hyperparameter_tunning(self,
                                model_param, 
                                train_data):
        """
        DESCRIPTION:
            Internal function performs hyperparameter tuning on 
            ML models for regression/classification/clustering problems.
         
        PARAMETERS:
            model_param
                Required Argument.
                Specifies the eval_params argument for GridSearch.
                Types: dict
                
            train_data:
                Required Argument.
                Specifies the training datasets.
                Types: tuple of Teradataml DataFrame
            
        RETURNS:
            pandas DataFrame containing, trained models information.
        
        RAISES:
            ValueError
            
        EXAMPLES:
            >>> models_df = self._hyperparameter_tunning(model_param={'name': 'xgboost', 'max_depth': (5, 7, 10)}, train_data=(lasso_train_data, rfe_train_data, pca_train_data))
        """ 
        # Passing verbose value based on user input
        if self.verbose > 0:
            print(" " *200, end='\r', flush=True)
            verbose = 1
        else:
            verbose = 0
        
        # Hyperparameter tunning
        # Parallel run opens multiple connections for parallel execution, 
        # but volatile tables are not accessible across different sessions. 
        # Therefore, execution is performed sequentially by setting run_parallel=False.

        run_parallel = configure.temp_object_type != TeradataConstants.TERADATA_VOLATILE_TABLE

        if not self.cluster:
            # Mapping model names to functions
            model_to_func = {"glm": GLM, "svm": SVM, 
                             "xgboost": XGBoost, "decision_forest": DecisionForest, "knn": KNN}

            # Setting eval_params for hpt.
            eval_params = _ModelTraining._eval_params_generation(model_param['name'], 
                                                                 self.target_column,
                                                                 self.task_type,
                                                                 self.id_column)

            # Input columns for model
            model_param['input_columns'] = self.features

            # Setting persist for model
            model_param['persist'] = self.persist

            self._display_msg(msg=f"Model training for {model_param['name']}", 
                              progress_bar=self.progress_bar,
                              show_data=True)
            
            # As we are using entire data for HPT training. So, 
            # passing prepared training data as test_data for KNN.
            if model_param['name'] == 'knn':
                model_param['test_data'] = train_data

            if self.task_type == "Classification":
                model_param['output_prob'] = True
                model_param['output_responses'] = self.output_response

            # Using RandomSearch for hyperparameter tunning when max_models is given.
            # Otherwise, using GridSearch for hyperparameter tunning.
            if self.max_models is not None:
                # Setting max_models for RandomSearch based on model name
                model_param['max_models'] = self.max_models_distribution[model_param['name']]
                # Defining RandomSearch with ML model based on Name, and max_models
                _obj = RandomSearch(func=model_to_func[model_param['name']],
                                    params=model_param,
                                    n_iter=model_param['max_models'])
            else:
                # Defining Gridsearch with ML model based on Name
                _obj = GridSearch(func=model_to_func[model_param['name']], 
                                  params=model_param)
                

            common_params = {
                "data": train_data,
                "evaluation_metric": self.stopping_metric,
                "early_stop": self.stopping_tolerance,
                "run_parallel": run_parallel,
                "sample_seed": self.seed,
                "sample_id_column": self.id_column,
                "discard_invalid_column_params": True,
                "stratify_column": self.startify_col,
                "verbose": verbose,
                "max_time": self.max_runtime_secs,
                "suppress_refer_msg": True
            }
            
            if model_param['name'] == 'knn':
                _obj.fit(**common_params)
            else:
                _obj.fit(**common_params, **eval_params)

            # Store the object in data_transform_dict
            self.data_transform_dict[f"hpt_object_{model_param['name']}"] = _obj

            # Getting all passed models
            model_info = _obj.model_stats.merge(_obj.models[_obj.models['STATUS']=='PASS'][['MODEL_ID', 'DATA_ID', 'PARAMETERS']],
                                                on='MODEL_ID', how='inner')
            if not model_info.empty:
                # Creating mapping data ID to feature selection method
                if self.enable_lasso:
                    data_id_to_table_map = {"DF_0": ('lasso', train_data[0]._table_name), 
                                            "DF_1": ('rfe', train_data[1]._table_name),
                                            "DF_2": ('pca', train_data[2]._table_name)}
                else:
                    data_id_to_table_map = {"DF_0": ('rfe', train_data[0]._table_name),
                                            "DF_1": ('pca', train_data[1]._table_name)}
                
                # Updating model stats with feature selection method and result table
                for index, row in model_info.iterrows():
                    model_info.loc[index, 'FEATURE_SELECTION'] = data_id_to_table_map[row['DATA_ID']][0]
                    model_info.loc[index, 'DATA_TABLE'] = data_id_to_table_map[row['DATA_ID']][1]
                    model_info.loc[index, 'RESULT_TABLE'] = _obj.get_model(row['MODEL_ID']).result._table_name
                    model_info.loc[index, 'model-obj'] = _obj.get_model(row['MODEL_ID'])
                
                # Dropping column 'DATA_ID'
                model_info.drop(['DATA_ID'], axis=1, inplace=True)

                model_info.insert(1, 'FEATURE_SELECTION', model_info.pop('FEATURE_SELECTION'))
                
                if not self.is_classification_type():
                    # Calculating Adjusted-R2 for regression
                    # Getting size and feature count for each feature selection method
                    methods = (['lasso', 'rfe', 'pca'] if self.enable_lasso else ['rfe', 'pca'])
                    size_map = {method : df.select(self.id_column).size for method, df in zip(methods, train_data)}
                    feature_count_map = {method : len(df.columns) - 2 for method, df in zip(methods, train_data)}
                    model_info['ADJUSTED_R2'] = model_info.apply(lambda row: 
                        1 - ((1 - row['R2']) * (size_map[row['FEATURE_SELECTION']] - 1) / 
                        (size_map[row['FEATURE_SELECTION']] - feature_count_map[row['FEATURE_SELECTION']] - 1)), axis=1)

                self._display_msg(msg="-"*100,
                                  progress_bar=self.progress_bar,
                                  show_data=True)
                self.progress_bar.update()

                return model_info
            # Returning None, if no model is passed
            return None
        else:
            import time
            from teradataml import td_sklearn as skl

            model_name = model_param['name']

            self._display_msg(msg=f"Model training for {model_name}",
                              progress_bar=self.progress_bar, show_data=True)

            if model_name == "kmeans":
                model_func = skl.KMeans()
                param_key = "n_clusters"
                pred_col = "kmeans_predict_1"
            elif model_name == "gaussianmixture":
                model_func = skl.GaussianMixture()
                param_key = "n_components"
                pred_col = "gaussianmixture_predict_1"
            else:
                raise ValueError(f"Unsupported model: {model_name}")

            model_param["input_columns"] = self.features
            model_param["persist"] = self.persist

            if self.max_models is not None:
                model_param['max_models'] = self.max_models_distribution[model_name]

                search_obj = RandomSearch(func=model_func,
                                          params=model_param['param_grid'],
                                          n_iter=model_param['max_models'])
            else:
                search_obj = GridSearch(func=model_func, params=model_param['param_grid'])
            
            search_obj.fit(data=train_data, evaluation_metric=self.stopping_metric,
                           early_stop=self.stopping_tolerance, run_parallel=run_parallel,
                           sample_seed=self.seed, verbose=verbose, max_time=self.max_runtime_secs)
            
            # Store the object in data_transform_dict
            self.data_transform_dict[f"hpt_object_{model_name}"] = search_obj

            model_df = search_obj.models[search_obj.models["STATUS"] == "PASS"]
            if model_df.empty:
                print("No models passed. Exiting.")
                self.progress_bar.update()
                return None

            model_stats = search_obj.model_stats
            model_info = model_stats.merge(model_df[['MODEL_ID', 'DATA_ID', 'PARAMETERS']],
                                           on="MODEL_ID", how="inner")
            
            if not model_info.empty:
                # Creating mapping data ID to feature selection method
                data_id_to_table_map = {"DF_0": ('pca', train_data[1]._table_name),
                                        "DF_1": ('non_pca', train_data[0]._table_name)}
                
                # Updating model stats with feature selection method and result table
                for index, row in model_info.iterrows():
                    model_info.loc[index, 'FEATURE_SELECTION'] = data_id_to_table_map[row['DATA_ID']][0]
                    model_info.loc[index, 'DATA_TABLE'] = data_id_to_table_map[row['DATA_ID']][1]
                    model_info.loc[index, 'model-obj'] = search_obj.get_model(row['MODEL_ID'])
                
                # Dropping column 'DATA_ID'
                model_info.drop(['DATA_ID'], axis=1, inplace=True)

                model_info.insert(1, 'FEATURE_SELECTION', model_info.pop('FEATURE_SELECTION'))
                
                self._display_msg(msg="-"*100,
                                  progress_bar=self.progress_bar,
                                  show_data=True)
                self.progress_bar.update()

                return model_info
            
            return None

        
    @staticmethod
    def _eval_params_generation(ml_name,
                                target_column,
                                task_type,
                                id_column):
        """
        DESCRIPTION:
            Internal function generates the eval_params for 
            different ML models.
         
        PARAMETERS:
            ml_name
                Required Argument.
                Specifies the ML name for eval_params generation.
                Types: str

            target_column
                Required Argument.
                Specifies the target column.
                Types: str
            
            task_type:
                Required Argument.
                Specifies the task type for AutoML, whether to apply regresion 
                or classification on the provived dataset.
                Permitted Values: "Regression", "Classification"
                Types: str
            
            id_column:
                Required Argument.
                Specifies the ID column for eval_params generation.
                Types: str

        RETURNS:
            dict containing, eval_params for ML model.
        
        RAISES:
            None
            
        EXAMPLES:
            >>> _ModelTraining._eval_params_generation(ml_name="decision_forest", 
            ...                                        target_column="target_class", 
            ...                                        task_type="Classification",
            ...                                        id_column="id")
        """ 
        # Setting the eval_params
        eval_params = {"id_column": id_column,
                       "accumulate": target_column}
        
        model_type = {
            'xgboost': 'model_type',
            'glm': 'model_type',
            'decisionforest': 'tree_type',
            'svm': 'model_type',
            'knn': 'model_type'
        }

        ml_name = ml_name.replace('_', '').lower()

        # For Classification
        if task_type.lower() != "regression":
            eval_params[model_type[ml_name]] = 'Classification'
            eval_params['output_prob'] = True

            if ml_name == 'xgboost':
                eval_params['object_order_column'] = ['task_index', 'tree_num', 'iter','class_num', 'tree_order']

            elif ml_name == 'glm':
                eval_params['family'] = 'BINOMIAL'
            
        else:
        # For Regression
            eval_params[model_type[ml_name]] = 'Regression'

            if ml_name == 'xgboost':
                eval_params['object_order_column'] = ['task_index', 'tree_num', 'iter', 'tree_order']

            elif ml_name == 'glm':
                eval_params['family'] = 'GAUSSIAN'
                
        return eval_params