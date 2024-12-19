from Blog.tasks import generate_text_task

def generate_text(prompt, max_tokens=100, temperature=0.7):
    """
    Enqueue a background task to generate text and return the task ID.
    """
    task = generate_text_task.delay(prompt, max_tokens, temperature)
    return task.id  