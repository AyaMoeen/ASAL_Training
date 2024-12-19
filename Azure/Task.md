> Level: Easy.


Azure Client API 
--

Create a Serverless Azure Client API CLI using `httpx` for GET/POST RestAPI operation.

- all needed data: 
    - https://learn.microsoft.com/en-us/rest/api/azure/devops/?view=azure-devops-rest-7.2
    - https://learn.microsoft.com/en-us/rest/api/azure/devops/core/projects?view=azure-devops-rest-7.2
    - https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/work-items?view=azure-devops-rest-7.2
    - https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/wiql?view=azure-devops-rest-7.2
    - https://www.python-httpx.org/
    - https://www.python-httpx.org/async/
    - https://www.serverless.com/framework/docs
    - https://boto3.amazonaws.com/v1/documentation/api/latest/index.html

Phase 1: Pyhton CLI API
--
* Authorization:
  * Get API token from Azure DevOps RestAPI
  * Use AWS SSM Parameter Store or Secrets Manager to store and retrieve the Azure API token.
  * Read the keys and do the authorization when needed.
  * Use Pydantic to validate request and response payloads.

* CLI: Using Sync Httpx
  * Create/List/Get/Delete Azure Project.
    * CLI command to create will need to provide a project name.
    * CLI command to List will need to list all Azure projects for the user.
    * CLI command to Get will need to list info about the project and list a new list of operations.
    * CLI command to delete the project.
  
  * Create/List/Update/Get/Delete Work items:
    * Create a work items ( Task, Bug, ...) for the selected project.
    * https://learn.microsoft.com/en-us/rest/api/azure/devops/processes/work-item-types/list?view=azure-devops-rest-6.0&tabs=HTTP
    * List all work items for the selected project.
    * Update an item.
    * Delete an item.
    * Get an item.
  
  * Use SNS or SQS to send the above operation.
    * Each CLI command should send the correct data needed for the operation to be done.

  * Create/Update/Delete/Copy/Move/Replace can be done through the lambda.
  * Get/List can be done immediately because we need a real-time response.

   * Optional:
      *   copy/move/replace an item.


* AWS Services
  * Implement a lambda handler that can process the requested Azure operation.
  * Lambda handler will read from SNS or SQS the operations received from the CLI.

Phase 2: Dead Letter Queue.
-- 
  * Create a DLQ to receive failed processed messages.
    
Phase 3: Discord WebHook.
--

* send a notification on every op.

Phase 4: GitHub Action.
--
  * Create a GitHub action to run sanity checks.
    - Linter / static checker / unit-tests
  * (Optional) Create a deployment pipeline for dynamically deploying Lambda functions on code changes.

Side Task:
--

* Read and understand LZ77 Algo ( Must )
* XSS ( Must ).


Required Files.
-- 
These files are required for all Future tasks as well.

* Unit-Testing ( pytest ).
* PyDoc3
* Ruff
* pyproject.toml
* requirements.txt
* serverless.yml
* __init__.py files
