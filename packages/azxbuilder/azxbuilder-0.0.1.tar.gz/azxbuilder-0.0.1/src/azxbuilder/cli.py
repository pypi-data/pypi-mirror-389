import typer
from pathlib import Path
import os

from .parser import load_app_from_schema, SchemaError
from .generator import generate_main_py

app = typer.Typer()

@app.command()
def build(
    schema_path: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, readable=True, help="Path to the schema.py file."),
    output_dir: Path = typer.Option("generated_app", "--output-dir", "-o", help="Directory to save the generated application.")
):
    """
    Builds a full-stack application from a schema file.
    """
    typer.echo(f"Starting build process for schema: {schema_path}")

    try:
        # 1. Parse the schema
        typer.echo("Parsing schema...")
        loaded_app = load_app_from_schema(schema_path)
        typer.echo(f"[SUCCESS] Schema parsed successfully. Found app ''{loaded_app.name}'' with {len(loaded_app.models)} models.")

        # 2. Generate the code
        typer.echo("Generating backend code...")
        main_py_content = generate_main_py(loaded_app)
        
        # 3. Write the output
        typer.echo(f"Writing generated code to: {output_dir}")
        output_dir.mkdir(exist_ok=True)
        
        # Write main.py
        (output_dir / "main.py").write_text(main_py_content)

        typer.echo("[SUCCESS] Backend code generated successfully.")
        typer.secho("\nBuild complete! ", fg=typer.colors.GREEN)
        typer.echo(f"To run your app, navigate to ''{output_dir}'' and run: uvicorn main:app --reload")

    except SchemaError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"An unexpected error occurred: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()