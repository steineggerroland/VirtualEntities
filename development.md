## Frontend

### Translations

We are using babel extension for flask to translate the app.
New translations are added using pybabel CLI with

```shell
pybabel extract -F babel.cfg -o translations/messages.pot flaskr
```

The new translations have to be added to the existing ones

```shell
pybabel update -i translations/messages.pot -d translations
```

These translations have to be compiled to be used in the application

```shell
pybabel compile -d translations
```