from app import app


def make_shell_context():
    return dict(app=app)


if __name__ == '__main__':
    port = app.config.get('PORT', 5001)
    app.run(port=port)
