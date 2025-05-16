from huggingface_hub import HfApi


api = HfApi(token="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")
api.upload_folder(
    folder_path="Z:/hf-image-first-time-bk",
    repo_id="YSXysx/space_first_data_bk",
    repo_type="dataset",
)
