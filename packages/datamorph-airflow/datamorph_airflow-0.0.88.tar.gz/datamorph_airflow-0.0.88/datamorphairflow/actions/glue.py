from airflow.providers.amazon.aws.operators.glue import GlueJobOperator

from datamorphairflow.file_util import S3FileSystem
from datamorphairflow.hooks import WorkflowParameters


class DMAWSGlueRunNowJobOperator(GlueJobOperator):
    """
    Extension of aws glue run operator with custom status push to xcom
    """

    def __init__(self, run_job_kwargs=None,load_params_loc=None, *args, **kwargs):
        super().__init__(run_job_kwargs=run_job_kwargs, **kwargs)
        self.jar_params = None
        self.load_params_loc = load_params_loc
        if run_job_kwargs is None:
            run_job_kwargs = dict()
        self.run_job_kwargs = run_job_kwargs
        self.args = args
        self.kwargs = kwargs

    def execute(self, context):
        workflow_params = WorkflowParameters(context)
        params = workflow_params.get_params()
        print(params)
        params_key = "--params"
        params_value = ""


        # 1. Check if params is not empty
        # 2. If not empty, construct the required string/list "key1=value,key2=value"
        # 3. Update job run arguments with the constructed string above

        if params:
            for k,v in params.items():
                params_value = params_value + "," + f'{k}={v}'

        if params_key in self.run_job_kwargs:
            self.run_job_kwargs[params_key] += "," + params_value
        else:
            self.run_job_kwargs[params_key] = params_value

        print(self.run_job_kwargs)
        #conn_id = self.kwargs.get("conn_id")
        job_id = self.kwargs.get("job_name")
        task_id = f'{self.kwargs.get("task_id")}_custom'
        run_now = GlueJobOperator(task_id=task_id,job_name=job_id, script_args=self.run_job_kwargs, do_xcom_push=True).execute(context)
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




