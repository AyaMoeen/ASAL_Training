import click
from Azure.sqs import send_to_sqs
from Azure.read_token import read_token_from_parameter, read_webhookurl_from_parameter
from Azure.azure_devops_api import list_projects, get_project, list_work_items_azure, get_work_item_azure
from Azure.handler import send_discord_notification

DISCORD_WEBHOOK_URL = read_webhookurl_from_parameter()

@click.group()
def cli():
    """Azure DevOps Project CLI"""
    pass

TOKEN = read_token_from_parameter()

@cli.command(name='create_project')
@click.argument('name')
@click.option('--description', default="", help="Description of the project")
@click.option('--visibility', default="private", type=click.Choice(['private', 'public'], case_sensitive=False), help="Visibility of the project")
@click.option('--source-control', default="Git", type=click.Choice(['Git', 'TFVC'], case_sensitive=False), help="Version control type")
@click.option('--template-id', default="6b724908-ef14-45cf-84f8-768b5384da45", help="Process template ID") 
def create(name: str, description: str, visibility: str, source_control: str, template_id: str) ->None:
    """Create a new Azure DevOps project"""
    try:  
        send_to_sqs('create_project', {
            'name': name,
            'description': description,
            'visibility': visibility,
            'source_control': source_control,
            'template_id': template_id
        },
                    webhook = DISCORD_WEBHOOK_URL,
                    token = TOKEN,
                    message_group_id = 'create_project_group')
    except Exception as e:
        click.echo(f"Error: {e}")
        
@cli.command(name='list_project')
def list() -> None:
    """List all Azure DevOps projects"""
    try:
        response = list_projects(TOKEN)
        click.echo(f"Total Projects: {response.count}")
        for project in response.value:
            click.echo(f"ID: {project.id}, Name: {project.name}, State: {project.state}, Last Updated: {project.last_update_time}")
        send_discord_notification("Operation result: list project Successfully", webhook = DISCORD_WEBHOOK_URL)
    except Exception as e:
        click.echo(f"Error: {e}")
        send_discord_notification("Operation result: list project Failed", webhook = DISCORD_WEBHOOK_URL)
        

@cli.command(name='get_project')
@click.argument('project_id')
def get(project_id: str) -> None:
    """Get details of a specific Azure DevOps project"""
    try:
        response = get_project(TOKEN, project_id)
        click.echo(f"Project ID: {response.id}, Name: {response.name}, State: {response.state}, Last Updated: {response.last_update_time}")
        send_discord_notification("Operation result: get project Successfully", webhook = DISCORD_WEBHOOK_URL)
    except Exception as e:
        click.echo(f"Error: {e}")
        send_discord_notification("Operation result: get project Failed", webhook = DISCORD_WEBHOOK_URL)


@cli.command(name='delete_project')
@click.argument('project_id')
def delete(project_id: str) -> None:
    """Delete an Azure DevOps project"""
    try:
        send_to_sqs('delete_project', {'project_id': project_id}, token = TOKEN,
                    webhook = DISCORD_WEBHOOK_URL, message_group_id = 'delete_project_group')
    except Exception as e:
        click.echo(f"Error: {e}")
        
@cli.command(name='create_item')  
@click.argument('project_id')
@click.argument('work_item_type')
@click.argument('title')
def create_work_item(project_id: str, work_item_type: str, title: str) -> None:
    """Create a new Azure DevOps work item (Task, Bug, etc.) in the selected project."""
    try:
        send_to_sqs('create_item', {'project_id': project_id, 'work_item_type': work_item_type, 'title': title},
                    token=TOKEN,
                    webhook = DISCORD_WEBHOOK_URL,
                    message_group_id='create_work_item_group')
    except Exception as e:
        click.echo(f"Error: {e}")

@cli.command(name='list_item')
@click.argument('project_id')
@click.argument('ids')
def list_work_items(project_id: str, ids: str) -> None:
    """List Azure DevOps work items in the selected project."""
    try:
        response = list_work_items_azure(TOKEN, project_id, ids)
        click.echo(f"Total Work Items: {response['count']}")
        for item in response['value']:
            click.echo(f"ID: {item['id']}, Title: {item['fields']['System.Title']}")
        send_discord_notification("Operation result: list item Successfully", webhook = DISCORD_WEBHOOK_URL)
        
    except Exception as e:
        click.echo(f"Error: {e}")
        send_discord_notification("Operation result: list item Failed", webhook = DISCORD_WEBHOOK_URL)
        
@cli.command(name='get_item')
@click.argument('project_id')
@click.argument('work_item_id')
def get_work_item(project_id: str, work_item_id: int) -> None:
    """Get details of a specific Azure DevOps work item in the selected project."""
    try:
        response = get_work_item_azure(TOKEN, project_id, work_item_id)
        click.echo(f"Work Item ID: {response['id']}, Title: {response['fields']['System.Title']}")
        send_discord_notification("Operation result: get item Successfully", webhook = DISCORD_WEBHOOK_URL)
    except Exception as e:
        click.echo(f"Error: {e}")
        send_discord_notification("Operation result: get item Failed", webhook = DISCORD_WEBHOOK_URL)
        
@cli.command(name='delete_item')
@click.argument('project_id')
@click.argument('work_item_id')
def delete_work_item(project_id: str, work_item_id: int) -> None:
    """Delete an Azure DevOps work item in the selected project."""
    try:
        send_to_sqs('delete_item', {'project_id': project_id, 'work_item_id': work_item_id},
                    token=TOKEN,
                    webhook = DISCORD_WEBHOOK_URL,
                    message_group_id='delete_work_item_group')
    except Exception as e:
        click.echo(f"Error: {e}")

@cli.command(name='update_item')
@click.argument('project_id')
@click.argument('work_item_id')
@click.argument('title')
def update_work_item(project_id: str, work_item_id: int, title: str) -> None:
    """Update an Azure DevOps work item in the selected project."""
    try:
        send_to_sqs('update_item', {'project_id': project_id, 'work_item_id': work_item_id, 'title': title},
                    token=TOKEN,
                    webhook = DISCORD_WEBHOOK_URL,
                    message_group_id='update_work_item_group')
    except Exception as e:
        click.echo(f"Error: {e}")
        
        
if __name__ == '__main__':
    cli()
