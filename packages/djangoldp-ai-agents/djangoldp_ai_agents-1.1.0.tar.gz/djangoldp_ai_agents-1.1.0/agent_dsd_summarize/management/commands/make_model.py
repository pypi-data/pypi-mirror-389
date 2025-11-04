# import json
# import os

# import pandas as pd
# from datasets import Dataset
from django.core.management.base import BaseCommand

# from transformers import (DataCollatorForSeq2Seq, T5ForConditionalGeneration,
#                           T5Tokenizer, Trainer, TrainingArguments)


class Command(BaseCommand):
    help = "Trains and saves the DSD summarizer model."

    def handle(self, *args, **options):
        # base_path = os.path.join(os.path.dirname(__file__), "..", "..")

        # # Convert dataset into Hugging Face dataset
        # df = pd.read_csv(os.path.join(base_path, "dataset.csv"))
        # dataset = Dataset.from_pandas(df)

        # todo

        self.stdout.write(
            self.style.SUCCESS("Successfully did nothing.")
        )
