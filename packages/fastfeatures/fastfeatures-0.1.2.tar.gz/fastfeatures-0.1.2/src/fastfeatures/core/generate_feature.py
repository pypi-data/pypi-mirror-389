"""This module provides a CLI tool to generate a new feature."""
import os
import shutil
import click
import pkg_resources

def to_snake_case(name):
    """Converts a string to snake_case.

    Args:
        name: The string to convert.

    Returns:
        The snake_cased string.
    """
    return name.lower().replace(" ", "_").replace("-", "_")

def to_pascal_case(name):
    """Converts a string to PascalCase.

    Args:
        name: The string to convert.

    Returns:
        The PascalCased string.
    """
    return "".join(word.capitalize() for word in to_snake_case(name).split("_"))

def to_camel_case(name):
    """Converts a string to camelCase.

    Args:
        name: The string to convert.

    Returns:
        The camelCased string.
    """
    snake_case = to_snake_case(name)
    parts = snake_case.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])

def create_feature(feature_name):
    """Creates a new feature.

    This function copies the template_feature directory to a new feature directory
    and replaces the placeholders with the new feature name.

    Args:
        feature_name: The name of the feature to create.
    """
    project_root = os.getcwd()
    app_dir = os.path.join(project_root, 'app')
    features_dir = os.path.join(app_dir, 'features')

    snake_case_name = to_snake_case(feature_name)
    pascal_case_name = to_pascal_case(feature_name)
    camel_case_name = to_camel_case(feature_name)

    feature_dir = os.path.join(features_dir, snake_case_name)

    # Safety check: abort if feature directory already exists
    if os.path.exists(feature_dir):
        click.echo(f"Error: A feature with the name '{feature_name}' already exists at {feature_dir}. Aborting.", err=True)
        return

    # Copy template_feature
    template_dir = pkg_resources.resource_filename('fastfeatures', 'template_feature')
    shutil.copytree(template_dir, feature_dir)

    # Rename files
    os.rename(os.path.join(feature_dir, 'models', 'feature_name.py'), os.path.join(feature_dir, 'models', f'{snake_case_name}.py'))
    os.rename(os.path.join(feature_dir, 'services', 'feature_name_services.py'), os.path.join(feature_dir, 'services', f'{snake_case_name}_services.py'))

    # Replace placeholders
    for root, dirs, files in os.walk(feature_dir):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'r') as f:
                content = f.read()
            content = content.replace('feature_name', snake_case_name)
            content = content.replace('FeatureName', pascal_case_name)
            content = content.replace('featureName', camel_case_name)
            with open(file_path, 'w') as f:
                f.write(content)

@click.command()
def generate_feature_cli():
    """CLI tool to generate a new feature."""
    feature_name = ""
    while not feature_name:
        feature_name = click.prompt('Feature name', type=str)
        if not feature_name:
            click.echo("Feature name cannot be empty. Please provide a value.", err=True)

    create_feature(feature_name)
    click.echo(f"Successfully created feature '{feature_name}'")

if __name__ == '__main__':
    generate_feature_cli()
