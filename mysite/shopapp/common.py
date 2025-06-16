from csv import DictReader
from io import TextIOWrapper

from django.contrib.auth import get_user_model


User = get_user_model()
def save_csv_model(file, encoding, model):
    csv_file = TextIOWrapper(
        file,
        encoding=encoding,
    )

    reader = DictReader(csv_file)

    models = []
    for row in reader:
        if "user" in row:
            row["user"] = User.objects.get(pk=int(row["user"]))

        models.append(model(**row))
    model.objects.bulk_create(models)
    return models
