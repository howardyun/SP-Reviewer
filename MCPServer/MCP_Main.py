from huggingface_hub import HfApi

api = HfApi(token='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')

hf = HfApi()


Space_Info = api.space_info(repo_id='Lightricks/ltx-video-distilled')



print(Space_Info)
