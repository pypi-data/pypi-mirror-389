"""Contains classes used for logging ML models to the tracking server

The wrapper classes contained in this section allow for logging model artifacts from
a number of supported libraries. The `Wrapper.log_model` implementation in each library-specific
wrapper class takes care of serializing a trained ML model to disk, constructing an appropriate directory
structure, packaging all artifacts with additional necessary metadata and uploading it to S3 as a deployable
payload
"""

import os
import requests
from urllib3 import Retry
from .inference import *
import tarfile
import shutil
import uuid
import time
import joblib
from pathlib import Path

class Wrapper(object):
    """Base class for Cortex library wrappers
    
    This class is meant to be inherited and is NOT meant to be instantiated explicitly

    Args:
        client (cortex.cortex.CortexClient): An instance of the `cortex.cortex.CortexClient`
        ml_library (str): Name of the ML library the wrapper is meant to be used for
    """
    def __init__(self, client, ml_library):
        self.client = client
        """An instance of `cortex.cortex.CortexClient`"""
        self.library = ml_library
        """ML Library name"""

    def log_model(
        self, 
        model=None, 
        scratch_directory="model",
        signature=None, 
        run_name=None, 
        run_description=None, 
        cortex_experiment_id=None, 
        dataset_version_id=None,
        dataset_input_columns=None,
        dataset_output_columns=None,
        assets=None,
        inputExample=None,
        **kwargs):
        """Logs a trained ML model to the tracking server

        Args:
            model (object, optional): A trained ML model from a specific library. If no model object is passed here, then it is expected that the model will be provided among the assets.
            scratch_directory (str, optional): Temporary directory for saving the serialized model and other assets before upload
            signature (cortex.schemas.CortexSignature, optional): An instance of `cortex.schemas.CortexSignature` that describes the model's I/O schema
            run_name (str, optional): The name for this Run
            run_description (str, optional): The description for this Run
            cortex_experiment_id (str, optional): ID of the Cortex Experiment associated with this Run
            dataset_version_id (str, optional): ID of the Cortex Dataset this model was trained on
            dataset_input_columns (list of str, optional): List of dataset column names used as inputs for training
            dataset_output_columns (list of str, optional): List of dataset column names used as outputs for training
            assets (list of str or str, optional): Any files that should be added to the payload. You can either provide a directory path as a string, or a list of filenames.
        
        Returns:
            dict: A dictionary representing a logged Run

        Typical usage example:

            >>> client = CortexClient("MY-TOKEN-HERE")
            >>> run = client.pytorch.log_model(
                model,
                run_name = "Parameters, Metrics, Signature, Dataset",
                run_description = "Test run with Parameters, Metrics, Signature and Dataset",
                cortex_experiment_id = exp["_id"],
                signature = signature,
                dataset_version_id=cursor.dataset_version_id(),
                dataset_input_columns=list(X.columns),
                dataset_output_columns=list(y.columns)
            )

        Adding files in standard logging:

            >>> client = CortexClient("MY-TOKEN-HERE")
            >>> run = client.pytorch.log_model(
                model,
                run_name = "Custom Requirements",
                run_description = "Test run with a custom requirements.txt file",
                cortex_experiment_id = exp["_id"],
                signature = signature,
                assets = [
                    "some/path/to/requirements.txt",
                    "some/path/to/important-file.py"
                ]
            )

        Logging a model entirely from local files:

            >>> client = CortexClient("MY-TOKEN-HERE")
            >>> run = client.pytorch.log_model(
                run_name = "Local Files Only",
                run_description = "Logging a model by pointing to a directory with all of the necessary files",
                cortex_experiment_id = exp["_id"],
                assets = "some/path/to/my/directory"
            )
        """

        _assets = assets if assets is not None else []

        if model is None and (_assets == None or len(_assets) == 0):
            raise Exception("Both `model` and `assets` arguments cannot be empty. Please, provide one or the other (or both)")

        library_version, sdk_version = self._get_versions_metadata()

        # Create run
        run = self.client.create_run(
            name=run_name, 
            description=run_description, 
            experimentId=cortex_experiment_id, 
            signature=signature, 
            libraryName=self.library,
            libraryVersion=library_version,
            sdkVersion=sdk_version,
            datasetVersionId=dataset_version_id,
            dataset_input_columns=dataset_input_columns,
            dataset_output_columns=dataset_output_columns,
            inputExample=inputExample)
        
        # Build directory structure
        temp_folder = self._create_temp_directory(scratch_directory)
        run_folder = self._create_run_directory(temp_folder, run["_id"])

        # Serialize model
        if model is not None:
            self.serialize_model(model, run_folder)

        # Create tarball
        tarball_path = self._save_tarball(temp_folder, run_folder, _assets)

        # Upload tarball
        key = "models/{0}/{1}.tar.gz".format(self._make_S3_key_compatible(self.library), run["_id"])
        self._upload({key: tarball_path})

        # Update logged run with the S3 key
        self.client.update_payload_key(run["_id"], key)

        # Clear client metadata
        self.client.purge_metadata()

        # Clean up
        shutil.rmtree(temp_folder)

        return self.client.get_run_by_id(run["_id"])
    

    def _get_versions_metadata(self):
        # Log model to Cortex API
        library_version = self.get_library_version()
        sdk_version = self.get_sdk_version()

        return library_version, sdk_version
    
    def _create_run_directory(self, payload_dir, run_id):
        run_dir = os.path.join(payload_dir, run_id)
        os.mkdir(run_dir)

        return run_dir

    def _create_temp_directory(self, scratch_directory):
        # Create artifact directory
        temp_folder = os.path.join(scratch_directory, str(uuid.uuid4()))
        os.makedirs(temp_folder)

        return temp_folder
    
    def _save_tarball(self, payload_dir, run_dir, assets=None):
        """Saves all assets as a `.tar` archive"""
        print("payload_dir", payload_dir)
        print("run_dir", run_dir)
        
        _assets = assets if assets is not None else []
        asset_filenames = []

        if type(_assets) is list:
            for asset in _assets:
                asset_filenames.append(self._copy_file_to_directory(asset, run_dir))
        elif type(_assets) is str:
            try:
                asset_filenames.extend(self.copy_tree(_assets, run_dir))
            except:
                raise Exception("`assets` must be either a list of filepaths or a string cantaining a path to a directory")

        ## Write inference.py
        if "inference.py" not in asset_filenames:
            self.add_default_inference_py(run_dir)

        print("os.path.dirname(run_dir)", os.path.dirname(run_dir))

        tar_name = str(os.path.basename(run_dir)) + ".tar.gz"
        tar_path = os.path.join(payload_dir, tar_name)

        print("tar_name", tar_name)
        print("tar_path", tar_path)

        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(run_dir, arcname=os.path.sep)

        return tar_path


    def _upload(self, keys_dict):
        #print("headers", headers)

        keys_response = self.client.get_artifact_upload_urls(keys_dict.keys())
        uri_dict = {}
        
        for obj in keys_response:
            s3key = obj["key"]
            url = obj["url"]
            uri_dict[s3key] = url

        for key in keys_dict:
            filepath = keys_dict[key]
            url = uri_dict[key]

            if os.stat(filepath).st_size == 0:
                put_request = requests.put(url, "")
                #print("Empty put")
            elif os.stat(filepath).st_size < 1073741824:
                with open(filepath, "rb") as file:
                    put_request = requests.put(url, file)
            else:
                self.client.multi_part_upload(filepath, key)
                #print("Put something there")
            #print()
            put_request.raise_for_status()
        
        #print("UPLOADED!")

    def get_sdk_version(self):
        """Identifies the current version of the Cortex SDK

        Returns:
            str: Cotex SDK version
        """
        import cortex
        return cortex.__version__

        

    def _make_S3_key_compatible(self, string):
        nStr = string.lower()
        illegal = [".", " ", "@", "#", "%", "^", "*", ":", ";", "\\", "/"]
        for char in illegal:
            if char in nStr:
                nStr = nStr.replace(char, "-")

        return nStr
    
    def _copy_file_to_directory(self, filepath, target_directory):
        filepath = Path(filepath)
        filename = filepath.name
        new_path = os.path.join(target_directory, filename)

        shutil.copy(filepath, new_path)
        return filename
    
    def copy_tree(self, src, dst):

        all_files = []
        for root, dirs, files in os.walk(src):
            # Calculate the path relative to the source directory
            rel_path = os.path.relpath(root, src)
            # Create a corresponding directory in the destination
            dst_dir = os.path.join(dst, rel_path)

            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)

            # Copy each file in the current directory to the destination directory
            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(dst_dir, file)
                shutil.copy2(src_file, dst_file)
                all_files.append(file)
        
        return all_files


class PyTorch_Wrapper(Wrapper):
    """A wrapper class for logging PyTorch ML models

    This class is NOT meant to be instantiated directly. An instance of the `PyTorch_Wrapper` is created with each new
    `cortex.cortex.CortexClient` and is available under `cortex.cortex.CortexClient.pytorch`

    Typical usage example:

        >>> client = CortexClient("MY-TOKEN-HERE")
        >>> run = client.pytorch.log_model(
                model,
                run_name = "My PyTorch run",
                run_description = "Just testing some stuff out",
                cortex_experiment_id = exp["_id"],
                signature = signature
            )
    """
    def __init__(self, client):
        super(PyTorch_Wrapper, self).__init__(client, "PyTorch")

    def get_library_version(self):
        """Returns the version of the ML library
        
        This method is not meant to be called explicitly. The only reason why it was not made private
        via the `_` prefix, is because it has to be accessible from the parent class
        """
        import torch
        return torch.__version__
    

    def serialize_model(self, model, run_dir):
        import torch

        scripted_model = torch.jit.script(model)
        scripted_model.save(os.path.join(run_dir,'model.pt'))

    def add_default_inference_py(self, run_dir):
        """Saves the standard `inference.py` file for PyTorch models into the `run_dir` directory
        
        This method is not meant to be called explicitly. The only reason why it was not made private
        via the `_` prefix, is because it has to be accessible from the parent class
        """

        inference_path = os.path.join(run_dir, "inference.py")
        with open(inference_path, "w") as f:
            payload = PYTORCH_INFERENCE
            f.write(payload)


class Sklearn_Wrapper(Wrapper):
    """A wrapper class for logging Scikit-Learn ML models

    This class is NOT meant to be instantiated directly. An instance of the `Sklearn_Wrapper` is created with each new
    `cortex.cortex.CortexClient` and is available under `cortex.cortex.CortexClient.sklearn`

    Typical usage example:

        >>> client = CortexClient("MY-TOKEN-HERE")
        >>> run = client.sklearn.log_model(
                model,
                run_name = "My Scikit-Learn run",
                run_description = "Just testing some stuff out",
                cortex_experiment_id = exp["_id"],
                signature = signature
            )
    """
    def __init__(self, client):
        super(Sklearn_Wrapper, self).__init__(client, "Scikit-Learn")

    def get_library_version(self):
        """Returns the version of the ML library
        
        This method is not meant to be called explicitly. The only reason why it was not made private
        via the `_` prefix, is because it has to be accessible from the parent class
        """
        import sklearn
        return sklearn.__version__
    
    def serialize_model(self, model, run_dir):
        import sklearn
        joblib.dump(model, os.path.join(run_dir, "model.joblib"))

    def add_default_inference_py(self, run_dir):
        """Saves the standard `inference.py` file for Scikit-Learn models into the `run_dir` directory
        
        This method is not meant to be called explicitly. The only reason why it was not made private
        via the `_` prefix, is because it has to be accessible from the parent class
        """
        inference_path = os.path.join(run_dir, "inference.py")
        with open(inference_path, "w") as f:
            payload = SCIKIT_INFERENCE
            f.write(payload)

class TensorFlow_Wrapper(Wrapper):
    """A wrapper class for logging Tensorflow/Keras ML models

    This class is NOT meant to be instantiated directly. An instance of the `TensorFlow_Wrapper` is created with each new
    `cortex.cortex.CortexClient` and is available under `cortex.cortex.CortexClient.tensorflow`

    Typical usage example:

        >>> client = CortexClient("MY-TOKEN-HERE")
        >>> run = client.tensorflow.log_model(
                model,
                run_name = "My Tensorflow run",
                run_description = "Just testing some stuff out",
                cortex_experiment_id = exp["_id"],
                signature = signature
            )
    """
    def __init__(self, client):
        super(TensorFlow_Wrapper, self).__init__(client, "TensorFlow")

    def get_library_version(self):
        """Returns the version of the ML library
        
        This method is not meant to be called explicitly. The only reason why it was not made private
        via the `_` prefix, is because it has to be accessible from the parent class
        """
        import tensorflow
        return tensorflow.__version__
    
    def serialize_model(self, model, run_dir):
        """Serializes the Tensorflow model by calling the `model.save` method
        
        This method is not meant to be called explicitly. The only reason why it was not made private
        via the `_` prefix, is because it has to be accessible from the parent class"""

        import tensorflow
        major_version = tensorflow.__version__.split(".")[0]
        model.save(os.path.join(run_dir, major_version))

    def add_default_inference_py(self, run_dir):
        """This method does nothing, since Tensorflow models do not require an `inference.py` file to run
        
        This method is not meant to be called explicitly. The only reason why it was not made private
        via the `_` prefix, is because it has to be accessible from the parent class
        """
        pass


class XGBoost_Wrapper(Wrapper):
    """A wrapper class for logging XGBoost ML models

    This class is NOT meant to be instantiated directly. An instance of the `XGBoost_Wrapper` is created with each new
    `cortex.cortex.CortexClient` and is available under `cortex.cortex.CortexClient.xgboost`

    Typical usage example:

        >>> client = CortexClient("MY-TOKEN-HERE")
        >>> run = client.xgboost.log_model(
                model,
                run_name = "My XGBoost run",
                run_description = "Just testing some stuff out",
                cortex_experiment_id = exp["_id"],
                signature = signature
            )
    """
    def __init__(self, client):
        super(XGBoost_Wrapper, self).__init__(client, "XGBoost")

    def get_library_version(self):
        """Returns the version of the ML library
        
        This method is not meant to be called explicitly. The only reason why it was not made private
        via the `_` prefix, is because it has to be accessible from the parent class
        """
        import xgboost
        return xgboost.__version__

    def serialize_model(self, model, run_dir):
        """Serializes the XGBoost model by calling the `model.save_model` method"""
        import xgboost
        model.save_model(os.path.join(run_dir, "xgboost-model.model"))

    def add_default_inference_py(self, run_dir):
        """Saves the standard `inference.py` file for XGBoost models into the `run_dir` directory
        
        This method is not meant to be called explicitly. The only reason why it was not made private
        via the `_` prefix, is because it has to be accessible from the parent class
        """
        # inference_path = os.path.join(run_dir, "inference.py")
        # with open(inference_path, "w") as f:
        #     payload = XGBOOST_INFERENCE
        #     f.write(payload)
        print("Adding custom inference.py files to XGBoost models is temporarily disabled")


class PyFunc_Wrapper(Wrapper):
    """A wrapper class for logging Python functions

    This class is NOT meant to be instantiated directly. An instance of the `PyFunc_Wrapper` is created with each new
    `cortex.cortex.CortexClient` and is available under `cortex.cortex.CortexClient.pyfunc`

    Typical usage example:

        >>> client = CortexClient("MY-TOKEN-HERE")
        >>> run = client.pyfunc.log_model(
                run_name = "My Python Function",
                run_description = "Just testing some stuff out",
                cortex_experiment_id = exp["_id"],
                assets = [ "./inference.py" ]
            )
    """

    def __init__(self, client):
        super(PyFunc_Wrapper, self).__init__(client, "PyFunc")
        self.version = "1.0.0"

    def get_library_version(self):
        """Returns the version of the library
        
        This method is not meant to be called explicitly. The only reason why it was not made private
        via the `_` prefix, is because it has to be accessible from the parent class
        """
        
        return self.version
    
    def serialize_model(self, model, run_dir):
        raise Exception("PyFunc deployments do not rely on a model")
    
    def add_default_inference_py(self, run_dir):
        pass