from app import app


# эти переменные доступны внутри оболочки без явного импорта
def make_shell_context():
    return dict(app=app)
# app = create_app()

if __name__ == '__main__':
    app.run()
