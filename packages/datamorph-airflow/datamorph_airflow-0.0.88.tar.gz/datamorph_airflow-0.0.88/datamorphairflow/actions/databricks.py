from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator

from datamorphairflow.file_util import S3FileSystem
from datamorphairflow.hooks import WorkflowParameters


class DMDatabricksRunNowJobOperator(DatabricksRunNowOperator):
    """
    Extension of databricks run now operator with custom status push to xcom
    """

    def __init__(self, jar_params=None, load_params_loc=None, *args, **kwargs):
        super().__init__(jar_params=jar_params, **kwargs)
        self.jar_params = None
        self.load_params_loc = load_params_loc
        # super().__init__(do_xcom_push=True, *args, **kwargs)
        # conn_id = databricks_conn_id
        if jar_params is None:
            jar_params = []
        self.jar_params = jar_params
        self.args = args
        self.kwargs = kwargs

    def execute(self, context):
        workflow_params = WorkflowParameters(context)
        params = workflow_params.get_params()
        print(params)
        param_list = []

        # 1.check if params is not empty
        # 2. If not empty, construct the required string/list "--params key=value"
        # 3. append list to job_param list
        if params:
            for k,v in params.items():
                param_list.append("--params")
                param_list.append(f'{k}={v}')
        if self.jar_params:
            self.jar_params.extend(param_list)
        else:
            self.jar_params = param_list
        print(self.jar_params)
        conn_id = self.kwargs.get("databricks_conn_id")
        job_id = self.kwargs.get("job_id")
        task_id = f'{self.kwargs.get("task_id")}_custom'
        #todo   add databricks retry etc
        run_now = DatabricksRunNowOperator(task_id=task_id,job_id=job_id,databricks_conn_id=conn_id, jar_params=self.jar_params, do_xcom_push=True).execute(context)
        #super(DMDatabricksRunNowJobOperator, self).execute(context)
        run_id = context["task_instance"].xcom_pull(self.task_id, key="run_id")
        self.log.info(run_id)
        self.log.info(self.run_id)
        # check if load params loc is specified
        # if specified, load the params from s3 location
        # print the params
        if self.load_params_loc:
            s3resource = S3FileSystem(context)
            params_from_file=s3resource.readJsonFromS3AsDict(self.load_params_loc)
            if params_from_file:
                workflow_params.update(params_dict=params_from_file)
            params = workflow_params.get_params()
            print("Parameters after run:")
            print(params)



class DMDatabricksPythonRunNowJobOperator(DatabricksRunNowOperator):
    """
    Extension of databricks run now operator with custom status push to xcom
    """

    def __init__(
            self, *args, **kwargs
    ):
        super().__init__(do_xcom_push=True, *args, **kwargs)
        # self.databricks_conn_id = databricks_conn_id

    def execute(self, context):
        super(DMDatabricksPythonRunNowJobOperator, self).execute(context)
        run_id = context["task_instance"].xcom_pull(self.task_id, key="run_id")
        self.log.info(run_id)
        self.log.info(self.run_id)

