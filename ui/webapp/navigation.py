def build_navigation_context() -> dict:
    return {
        "app_name": "AI Tool Gateway",
        "product_nav": [
            {"label": "Home", "endpoint": "app_pages.home"},
            {"label": "Projects", "endpoint": "projects_pages.projects"},
            {"label": "New Project", "endpoint": "projects_pages.create_project"},
            {"label": "Account", "endpoint": "account.overview"},
            {"label": "Settings", "endpoint": "app_pages.settings"},
            {"label": "Logout", "endpoint": "public.logout"},
        ],
        "project_nav": [
            {"label": "Workspace", "endpoint": "project.workspace"},
            {"label": "Activity", "endpoint": "project.activity"},
            {"label": "Settings", "endpoint": "project.settings"},
        ],
    }
