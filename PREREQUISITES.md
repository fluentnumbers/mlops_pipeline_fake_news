<!-- vscode-markdown-toc -->
- [Pre-requisites](#pre-requisites)
	- [Kaggle](#kaggle)
	- [Google Cloud](#google-cloud)

<!-- vscode-markdown-toc-config
	numbering=false
	autoSave=true
	/vscode-markdown-toc-config -->
<!-- /vscode-markdown-toc -->

# Pre-requisites
![Kaggle](https://img.shields.io/badge/Kaggle-035a7d?style=for-the-badge&logo=kaggle&logoColor=white) ![Google Cloud](https://img.shields.io/badge/GoogleCloud-%234285F4.svg?style=for-the-badge&logo=google-cloud&logoColor=white)


## <a name='Kaggle'></a>Kaggle
- Create a [Kaggle](https://www.kaggle.com/) account
- Go to user settings and create an API token which will be a *.json* file with your username and token inside:
```
{"username":"yourusername","key":"somealphanumericstring"}
```
- Later on: you will need to [copy these credentials into a .env file](./infrastructure/README.md/#env-file).

## <a name='GoogleCloud'></a>Google Cloud
- Make a free Google account and login into [Google Cloud Platform](https://console.cloud.google.com)
- Create a new GCP project
	- Instructions: [Create a Google Cloud project](https://developers.google.com/workspace/guides/create-project)
- Create a Service account
	- Instructions: [Create service accounts](https://cloud.google.com/iam/docs/service-accounts-create)
- When granting access rights choose **Owner** to avoid issues with API functionality.
  > **Warning**
  > **In a real project, access rights must be more fine-tuned for security purposes.**

- Download credentials .json file
	- Put generated file somewhere, but ***make sure not to commit it accidentally to your repo** (add the filename to .gitignore if you store it in the git repo).
	- Later on: you need to [copy these credentials to the VM](./infrastructure/README.md#move-credentials-to-the-vm).


[Previous: Main README](./README.md) | [Next: Infrastructure](./infrastructure/README.md)
