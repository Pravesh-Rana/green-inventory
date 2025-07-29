# run.py (Final Corrected Version)

from app import create_app, db
from app.models import ProductType, InventoryItem

# 1. Create the application instance using the factory
app = create_app()

# 2. Define the shell context processor using the created 'app' instance
@app.shell_context_processor
def make_shell_context():
    """Makes these models available in the 'flask shell' for easy testing."""
    return {'db': db, 'ProductType': ProductType, 'InventoryItem': InventoryItem}

# 3. Run the application
if __name__ == '__main__':
    app.run(debug=True)