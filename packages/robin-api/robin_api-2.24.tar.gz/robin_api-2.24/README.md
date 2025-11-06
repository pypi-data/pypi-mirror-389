# RobinApi Framework

**Description:**  
RobinApi Framework is a comprehensive solution designed to facilitate efficient interaction with Large Language Model (LLM) APIs and advanced vector data management. This framework provides robust tools for uploading and storing files in an optimized vector database, allowing users to fully leverage content-based search and retrieval. Users can upload documents via the API, which are then stored in a vector database, enabling them to query for the most similar phrases. Moreover, RobinApi Framework includes dedicated endpoints for complex queries, enabling users to extract valuable insights and conduct in-depth analyses of the stored data. Ideal for developers looking to integrate LLM capabilities into their applications and efficiently manage large volumes of data, RobinApi Framework stands out for its flexibility, scalability, and ease of use.

**Key Features:**

- **LLM API Consumption:** Optimized interfaces for interacting with language models, facilitating integration and real-time response handling.
- **Vector Database File Management:** Efficient file uploading, storage, and management with vector search, perfect for applications requiring fast and accurate access to large volumes of data.
- **Query Endpoints:** Specialized functionalities for asking questions and retrieving responses based on stored data, supporting a wide range of analytical and search queries.
- **High Configurability and Security:** Detailed parameter configuration and advanced security protocols to protect information and ensure performance.



### Set an environment variable in your OS:


**macOS:**
**Linux:**
```bash
export API_KEY="API_KEY"
```

**Windows:**
```cmd
set API_KEY "YourAPIKeyHere"
```
## Api Conect Internet
### Request Stream
```python
from robin_api import RobinAIClient


#This step is not necesary if you set this environment variable in your os
client = RobinAIClient(api_key="API_KEY")
### Example Code


from robin_api import RobinAIClient

# Initialize the client with an API key
client = RobinAIClient(api_key="API_KEY")

# Create a conversation prompt
value = [
    {
        "role": "system",
        "content": "system_prompt"
    },
    {
        "role": "user",
        "content": "Give a hello word in python"
    }
]


# Print each chunk of the streamed response and the end print the metrics
stream = client.completions.create_stream(model="ROBIN_4", 
                            conversation = value, 
                            max_tokens = 512, 
                            save_response = False,
                            temperature=1)

for chunk in stream:
    if not chunk.choices[0].finish_reason:
        print(chunk.choices[0].delta.content, end="")
    else:
        print(chunk.details, end="")
```

### Generating a Complete Response

```python
response = client.completions.create(
    model="ROBIN_4",
    conversation=value, 
    max_tokens=512, 
    save_response=False, 
    temperature=1
)

# Print the entire response
print(response.choices[0].delta.content, end="")
```

**Parameters:**

- **model**: Specifies which LLM model to use, e.g., "ROBIN_4".

- **conversation**: An array of messages that form the prompt conversation.

- **max_tokens**: Maximum number of tokens for the response.

- **save_response**: If `False`, does not store the response in persistent storage.

- **temperature**: Controls the randomness of responses; values close to 1 are more diverse.




### Text to Image
To generate an image from text using RobinApi Framework, you can use the following code snippet:

```python
from robin_api import RobinAIClient

client = RobinAIClient(api_key="API_KEY")

image = client.completions.text_to_image("Hello, how are you?")
print(image.url)
```

## Folder Api
### Upload a file from a web URL file

This function allows you to upload files to the vector database. When you upload a file without specifying a `folder_id`, a new folder is automatically created. You can then use that `folder_id` to add more files to the same folder and collection.

```python

# Upload first file - a new folder will be created automatically
folder_information = client.files.upload_file(
    url="https://arxiv.org/pdf/2302.13971.pdf",
    collection_name="my_collection"
)

# Get the folder_id from the response to use it later
folder_id = folder_information.folder.apiFolderId
print(f"Created folder ID: {folder_id}")

# Add more files to the same folder and collection
folder_information2 = client.files.upload_file(
    url="https://ecommercewgs.s3.amazonaws.com/2025-11-03/bBIPhWpSc9nKmcfZzM2IaEYkjAhq6bqrz6SXQLsL.json",
    folder_id=folder_id,  # Use the folder_id from the first upload
    collection_name="my_collection"  # Same collection name
)

# Upload file with URL and specify existing folder and collection
folder_information = client.files.upload_file(
    url="https://arxiv.org/pdf/2302.13971.pdf",
    folder_id="existing_folder_id",
    collection_name="my_collection"
)



```

**Example Response:**

```python
ResponseFile(
    folder=Folder(
        apiFolderId='cac5925e-fc9b-4024-8596-0bd7e9b46850',
        createdAt='2025-11-06T02:39:24.000000Z'
    ),
    file=File(
        url='https://ecommercewgs.s3.amazonaws.com/2025-11-03/bBIPhWpSc9nKmcfZzM2IaEYkjAhq6bqrz6SXQLsL.json',
        tokens=50,
        documentId='e54923ce-b76d-4554-8720-3f39d90e2797',
        createdAt='2025-11-06T02:39:24.000000Z'
    )
)

# Access folder ID
folder_id = folder_information.folder.apiFolderId

# Access file information
file_url = folder_information.file.url
document_id = folder_information.file.documentId
```

**Parameters:**

- **url** (optional):  URL of the document to upload. Either `url` or `file_id` must be provided.
- **file_id** (optional): The unique identifier of the file already stored in the cloud. Either `url` or `file_id` must be provided.
- **folder_id** (optional): The folder ID where the file will be stored. **If not specified, a new folder will be created automatically**. Use the `apiFolderId` from the response to add more files to the same folder.
- **collection_name** (required): The name of the collection where the document will be indexed in the vector database. Use the same `collection_name` and `folder_id` to add more files to the same collection.

**Important Notes:**

- When you upload a file without `folder_id`, a new folder is automatically created. Save the `folder_id` (accessible via `response.folder.apiFolderId`) to add more files to the same folder.
- To add more files to an existing folder and collection, provide both the `folder_id` from the previous upload and the same `collection_name`.


### Upload Web Page information Function
This function allows uploading information from a web page into the system, storing the relevant data in an organized structure for subsequent analysis and retrieva

```python
folder_information = client.files.upload_web_page_information(
    url="https://web.com/example",
    deep_level=1,
    max_links=10
)

folder_information = client.files.upload_web_page_information(
    url="https://web.com/example",
    deep_level=1,
    folder_id="FolderId",
    max_links=5
)


```
**Parameters:**

- **url**: The URL of the web page from which to extract information.

- **deep_level** (optional): The depth level for data extraction. A higher value results in more exhaustive exploration.
  - **Accepted Values**: `1`, `2`, `3`.
  - **Default**: `1`.

- **folder_id** (optional): The folder ID where the extracted information will be stored. If not specified, a new folder will be created.

**Response Structure:**

```python
ApiResponse(
    status_code=200,
    message={
        'folder': {
            'apiFolderId': 'FolderId',
            'createdAt': '2024-05-09T20:26:55.000000Z'
        },
        'file': {
            'url': 'https://example.com',
            'tokens': None,
            'documentId': None,
            'createdAt': '2024-05-09T20:29:12.000000Z'
        }
    }
)
```


- **folder**: Contains details about the folder where the web page data is stored.
  - **apiFolderId**: The unique identifier of the folder created or used for storing the extracted information.
  - **createdAt**: The timestamp indicating when the folder was created, in ISO 8601 format.

- **file**: Provides information about the extracted web page.
  - **url**: The URL of the web page that was uploaded for data extraction.
  - **tokens**: This field will be populated once the indexing process is complete, representing the total number of tokens extracted from the web page content.
  - **documentId**: Will be created after indexing, serving as a unique identifier for the document.
  - **createdAt**: The timestamp indicating when the file was created, in ISO 8601 format.



### Upload local files
```python
folder_information = client.files.upload_local_file(file="./LICENSE", purpose="store in datalake")
print(folder_information)
print(folder_information.file_id) 
```
**Parameters:**

- **file**: Path of the local file to be uploaded.
- **purpose**: Description of the purpose for uploading the file, such as "store in datalake".





### Finding Similar Sentences in the Folder


```python

# Get similar sentences without collection
similar_sentences = client.files.get_similar_sentences( 
    query = "What are the practical implications of the findings in the document?",
    top = 15,
    api_folder_id = "YOUR_API_FOLDER",
    similarity_threshold = 0.4 )

# Get similar sentences with collection
similar_sentences = client.files.get_similar_sentences( 
    query = "What are the practical implications of the findings in the document?",
    top = 15,
    api_folder_id = "YOUR_API_FOLDER",
    collection_name = "my_collection",
    similarity_threshold = 0.4 )

```
**Parameters:**

- **query**: Text query to search for similar sentences.

- **top**: Number of top matching sentences to return.
  - **Default**: `10`

- **api_folder_id**: Unique identifier for the folder where the document is stored.

- **similarity_threshold**: Minimum similarity score required for sentences to be returned.
  - **Default**: `0.4`

- **collection_name** (optional): The name of the collection to search within. If not specified, searches across all collections in the folder.



**Example response**
```json
{
    "sentences": [
        {
            "sentence": "and Denny Zhou. 2022. Self-consistency improves\nchain of thought reasoning in language models.\nJason Wei, Yi Tay, Rishi Bommasani, Colin Raffel,\nBarret Zoph, Sebastian Borgeaud, Dani Yogatama,\nMaarten Bosma, Denny Zhou, Donald Metzler, et al.\n2022. Emergent abilities of large language models.\narXiv preprint arXiv:2206.07682 .\nGuillaume Wenzek, Marie-Anne Lachaux, Alexis Con-\nneau, Vishrav Chaudhary, Francisco Guzmán, Ar-\nmand Joulin, and Edouard Grave. 2020. CCNet: Ex-\ntracting high quality monolingual datasets from web\ncrawl data. In Language Resources and Evaluation\nConference .\nCarole-Jean Wu, Ramya Raghavendra, Udit Gupta,\nBilge Acun, Newsha Ardalani, Kiwan Maeng, Glo-\nria Chang, Fiona Aga, Jinshi Huang, Charles Bai,\net al. 2022. Sustainable ai: Environmental implica-\ntions, challenges and opportunities. Proceedings of\nMachine Learning and Systems , 4:795–813.\nRowan Zellers, Ari Holtzman, Yonatan Bisk, Ali\nFarhadi, and Yejin Choi. 2019. Hellaswag: Can a\nmachine really ﬁnish your sentence? arXiv preprint\narXiv:1905.07830 .\nAohan Zeng, Xiao Liu, Zhengxiao Du, Zihan Wang,\nHanyu Lai, Ming Ding, Zhuoyi Yang, Yifan Xu,\nWendi Zheng, Xiao Xia, Weng Lam Tam, Zixuan\nMa, Yufei Xue, Jidong Zhai, Wenguang Chen, Peng\nZhang, Yuxiao Dong, and Jie Tang. 2022. Glm-\n130b: An open bilingual pre-trained model.\nBiao Zhang and Rico Sennrich. 2019. Root mean\nsquare layer normalization. Advances in Neural In-\nformation Processing Systems , 32.\nSusan Zhang, Stephen Roller, Naman Goyal, Mikel\nArtetxe, Moya Chen, Shuohui Chen, Christopher De-\nwan, Mona Diab, Xian Li, Xi Victoria Lin, et al.\n2022. Opt: Open pre-trained transformer language\nmodels. arXiv preprint arXiv:2205.01068 .",
            "score": 0.4931640625,
            "metadata": {
                "document_id": "DocumentId",
                "element_id": "517af0fd-fed7-4682-ac9d-46e866531839",
                "doc_id": "aaa6b579-a71f-4edc-b1e9-8064721a5a98",
                "file_name": "zqA6c.pdf",
                "page_label": "16",
                "source_url": "https://arxiv.org/pdf/2302.13971.pdf"
            }
        },
        {
            "sentence": "7B 13B 33B 65B\nAll 66.0 64.7 69.0 77.5\nher/her/she 65.0 66.7 66.7 78.8\nhis/him/he 60.8 62.5 62.1 72.1\ntheir/them/someone 72.1 65.0 78.3 81.7\nher/her/she ( gotcha ) 64.2 65.8 61.7 75.0\nhis/him/he ( gotcha ) 55.0 55.8 55.8 63.3\nTable 13: WinoGender. Co-reference resolution ac-\ncuracy for the LLaMA models, for different pronouns\n(“her/her/she” and “his/him/he”). We observe that our\nmodels obtain better performance on “their/them/some-\none’ pronouns than on “her/her/she” and “his/him/he’,\nwhich is likely indicative of biases.\nTruthful Truthful*Inf\nGPT-31.3B 0.31 0.19\n6B 0.22 0.19\n175B 0.28 0.25\nLLaMA7B 0.33 0.29\n13B 0.47 0.41\n33B 0.52 0.48\n65B 0.57 0.53\nTable 14: TruthfulQA. We report the fraction of truth-\nful and truthful*informative answers, as scored by spe-\ncially trained models via the OpenAI API. We follow\nthe QA prompt style used in Ouyang et al. (2022), and\nreport the performance of GPT-3 from the same paper.\nIn Table 14, we report the performance of our\nmodels on both questions to measure truthful mod-\nels and the intersection of truthful and informative.\nCompared to GPT-3, our model scores higher in\nboth categories, but the rate of correct answers is\nstill low, showing that our model is likely to hallu-\ncinate incorrect answers.\n6 Carbon footprint\nThe training of our models have consumed a mas-\nsive quantity of energy, responsible for the emis-\nsion of carbon dioxide. We follow the recent liter-\nature on the subject and breakdown both the total\nenergy consumption and the resulting carbon foot-\nprint in Table 15. We follow a formula for Wu et al.\n(2022) to estimate the Watt-hour, Wh, needed to\ntrain a model, as well as the tons of carbon emis-\nsions, tCO 2eq. For the Wh, we use the formula:\nWh =GPU-h×(GPU power consumption )×PUE,where we set the Power Usage Effectiveness (PUE)\nat1.1. The resulting carbon emission depends on\nthe location of the data center used to train the net-\nwork. For instance, BLOOM uses a grid that emits\n0.057 kg CO 2eq/KWh leading to 27 tCO 2eq and\nOPT a grid that emits 0.231 kg CO 2eq/KWh, lead-\ning to 82 tCO 2eq. In this study, we are interested in\ncomparing the cost in carbon emission of training\nof these models if they were trained in the same\ndata center. Hence, we do not take the location\nof data center in consideration, and use, instead,\nthe US national average carbon intensity factor of\n0.385 kg CO 2eq/KWh. This leads to the following\nformula for the tons of carbon emissions:\ntCO2eq=MWh×0.385.\nWe apply the same formula to OPT and BLOOM\nfor fair comparison. For OPT, we assume training\nrequired 34 days on 992 A100-80B (see their logs4).\nFinally, we estimate that we used 2048 A100-80GB\nfor a period of approximately 5 months to develop\nour models. This means that developing these mod-\nels would have cost around 2,638 MWh under our\nassumptions, and a total emission of 1,015 tCO 2eq.\nWe hope that releasing these models will help to\nreduce future carbon emission since the training is\nalready done, and some of the models are relatively\nsmall and can be run on a single GPU.\n7 Related work\nLanguage models are probability distributions\nover sequences of words, tokens or charac-\nters (Shannon, 1948, 1951). This task, often framed\nas next token prediction, has long been considered a\ncore problem in natural language processing (Bahl\net al., 1983; Brown et al., 1990). Because Turing\n(1950) proposed to measure machine intelligence\nby using language through the “imitation game”,\nlanguage modeling has been proposed as a bench-\nmark to measure progress toward artiﬁcial intelli-\ngence (Mahoney, 1999).\nArchitecture. Traditionally, language models\nwere based on n-gram count statistics (Bahl\net al., 1983), and various smoothing techniques\nwere proposed to improve the estimation of rare\nevents (Katz, 1987; Kneser and Ney, 1995). In the\npast two decades, neural networks have been suc-\ncessfully applied to the language modelling task,\n4https://github.com/facebookresearch/metaseq/\ntree/main/projects/OPT/chronicles",
            "score": 0.464111328125,
            "metadata": {
                "document_id": "DocumentId",
                "element_id": "517af0fd-fed7-4682-ac9d-46e866531839",
                "doc_id": "aaa6b579-a71f-4edc-b1e9-8064721a5a98",
                "file_name": "zqA6c.pdf",
                "page_label": "10",
                "source_url": "https://arxiv.org/pdf/2302.13971.pdf"
            }
        }
    ]
}
```




### Getting Context-Based Responses from the Folder

```python
answer = client.files.get_response_similar_sentences(
    model="ROBIN_4",
    max_new_tokens = 200,
    top = 15,
    api_folder_id = "YOUR_FOLDER_ID",
    similarity_threshold = 0.4,
    conversation=value,
    only_with_context = True)
```


**Parameters:**

- **model**: Specifies the LLM model to use.

- **max_new_tokens**: Maximum number of tokens to generate in the new response.

- **top**: Number of top matches to return.

- **api_folder_id**: Unique identifier for the folder containing the documents.

- **similarity_threshold**: Minimum similarity score required for sentences to be returned.

- **conversation**: An array of messages forming the conversation context.

- **only_with_context**: If `True`, generates a response only if relevant context is found in the folder.



**Example response**
print(answer.message.choices[0].message.content)
```json
{
    "choices": [
        {
            "finish_reason": "stop",
            "index": 0,
            "message": {
                "content": "According to the context provided, LLAMA (sometimes written as LLaMA) refers to a language model. It is compared to other language models such as PaLM and LaMDA in terms of performance on quantitative reasoning datasets and code generation tasks. The specific details about what \"LLAMA\" stands for or its unique characteristics are not provided in the context.",
                "role": "assistant"
            },
            "logprobs": null
        }
    ],
    "created": 1715054099,
    "id": "messageId",
    "model": "ROBIN_4",
    "object": "chat.completion",
    "usage": {
        "completion_tokens": 76,
        "prompt_tokens": 2915,
        "total_tokens": 2991
    }
}
```

### Getting Context-Based stream response from the Folder


```python
stream = client.files.get_response_similar_sentences_stream(
    model="ROBIN_4",
    max_new_tokens = 200,
    top = 1,
    api_folder_id = "YOUR_API_FOLDER",
    similarity_threshold = 0.4,
    conversation=value,
    only_with_context = True)

for chunk in stream:
    if not chunk.choices[0].finish_reason:
        print(chunk.choices[0].delta.content, end="")
    else:
        print(chunk.details, end="")
```



---

### Fetching Files from a Folder

Retrieve a list of files stored in a specific folder using the RobinApi Framework.

```python
from robin_api import RobinAIClient

# Initialize the client with an API key
client = RobinAIClient(api_key="YOUR_API_KEY")

# Fetch the list of files from a folder
folder_id = "YOUR_API_FOLDER"
documents = client.files.get_folder_files(api_folder_id=folder_id)

# Fetch files from a specific collection
documents = client.files.get_folder_files(
    api_folder_id=folder_id,
    collection_name="my_collection"
)

# Print the list of files
print(f"Count documents: {documents.count}")
print("Files in the folder:")
for document in documents.docs:
    print(f"""
           Sentence: {document.sentence },
           Document ID: {document.metadata.document_id}, 
           Element ID: {document.metadata.element_id},
           Doc ID: {document.metadata.doc_id},
           Page Label: {document.metadata.page_label} ,
           Source Url: {document.metadata.source_url} ,""")

```

**Parameters:**

- **api_folder_id**: The unique identifier for the folder from which to retrieve the files.

- **collection_name** (optional): The name of the collection to filter files. If not specified, returns all files from the folder.

**Response Structure:**

The response contains details about the files, including their IDs, names, URLs, and creation timestamps. The metadata includes:
- **document_id**: Unique identifier for the document
- **element_id**: Unique identifier for the element
- **doc_id**: Document ID
- **file_name**: Name of the file
- **page_label**: Page number or label
- **source_url**: URL from which the document was uploaded

---

### Delete All Documents from a Collection

This function allows you to delete all documents from a specific collection in the vector database.

```python
from robin_api import RobinAIClient

# Initialize the client with an API key
client = RobinAIClient(api_key="YOUR_API_KEY")

# Delete all documents from a collection
result = client.files.delete_all_documents(
    folder_id="cac5925e-fc9b-4024-8596-0bd7e9b46850",
    collection_name="test_collection"
)

# Check the result
if result.status_code == 200:
    print("✅ Documentos eliminados exitosamente")
    print(result.message)
else:
    print(f"⚠️ Error: {result.status_code}")
    print(result.message)
```

**Parameters:**

- **folder_id**: The unique identifier for the folder containing the collection.
- **collection_name**: The name of the collection from which to delete all documents.

**Note:** The backend automatically obtains the `user_id` from the authentication token, so you don't need to provide it.

---

### Delete a Specific Element from a Collection

This function allows you to delete a specific element from a collection in the vector database by its element ID.

```python
from robin_api import RobinAIClient

# Initialize the client with an API key
client = RobinAIClient(api_key="YOUR_API_KEY")

# Delete a specific element from a collection
result = client.files.delete_element(
    folder_id="cac5925e-fc9b-4024-8596-0bd7e9b46850",
    collection_name="test_collection",
    element_id="51e97895-b31f-4c95-a1dc-511f7b5063d6"
)

# Check the result
if result.status_code == 200:
    print("✅ Elemento eliminado exitosamente")
    print(result.message)
else:
    print(f"⚠️ Error: {result.status_code}")
    print(result.message)
```

**Parameters:**

- **folder_id**: The unique identifier for the folder containing the collection.
- **collection_name**: The name of the collection from which to delete the element.
- **element_id**: The unique identifier of the element to delete.

**Note:** The backend automatically obtains the `user_id` from the authentication token, so you don't need to provide it.

---

This section provides a quick and clear explanation on how to use the RobinApi Framework to fetch files from a specific folder, including a code example and a brief description of the parameters and response structure.




## Fine-Tuning Functions

### upload_local_file

This endpoint allows you to upload datasets in CSV or Parquet format for the purpose of training or testing the model.

**Parameters:**

- **file**: Path to the local file to be uploaded.
  - **Type**: `str`
  - **Description**: The path to the CSV or Parquet file that you wish to upload.
- **purpose**: The purpose of uploading the file.
  - **Type**: `str`
  - **Accepted Values**: `"train"`, `"test"`
  - **Description**: Specifies whether the file is intended for training or testing the model.

**Example Usage:**

```python
folder_information = client.files.upload_local_file(file="./dataset.csv", purpose="train")
print(folder_information)
print(folder_information.file_id)
```

---

### star_fine_tuning

This function initiates fine-tuning of models through an API request to an external service. It supports specific tasks such as text classification, language modeling, or text-to-image generation.

#### Parameters:

- `model` (str): The name of the model to fine-tune.
- `task` (str): The type of task to perform. It must be one of the following: 'classification-text', 'language-modeling', or 'text-to-images'.
- `sub_category` (str): Sub-category associated with the task.
- `media_id` (str): Identifier of the media related to the task.
- `description` (str): Description of the task or fine-tuning to be performed.
- `params` (dict): Specific parameters required for the fine-tuning task.
- `params_input` (dict): Additional input parameters for the task.
- `params_output` (str): Specific output parameters expected.
- `extension` (str): Extension related to the task.

#### Supported Task Types:

The function supports the following task types (defined by the `task` parameter):

- **classification-text**: Fine-tuning for text classification tasks.
- **language-modeling**: Fine-tuning for language modeling.
- **text-to-images**: Fine-tuning for generating images from text.

#### Required Parameters:

Depending on the selected task (`task`), the function requires specific parameters within the `params` dictionary:

- **classification-text**:
  - `num_train_epochs` (int)
  - `per_device_train_batch_size` (int)
  - `per_device_eval_batch_size` (int)
  - `warmup_steps` (int)
  - `weight_decay` (float)
  - `logging_strategy` (str)
  - `logging_steps` (int)
  - `evaluation_strategy` (str)
  - `eval_steps` (int)
  - `save_strategy` (str)
  - `fp16` (bool)
  - `load_best_model_at_end` (bool)

- **language-modeling**:
  - `optim` (str)
  - `learning_rate` (float)
  - `max_grad_norm` (float)
  - `num_train_epochs` (int)
  - `evaluation_strategy` (str)
  - `eval_steps` (int)
  - `warmup_ratio` (float)
  - `save_strategy` (str)
  - `group_by_length` (bool)
  - `lr_scheduler_type` (str)

**Other Details:**

The `params` parameter must include all required parameters according to the selected task type. If any parameter is missing or does not match the expected type, a `ValueError` will be raised.

**Example Usage:**

```python
# Example usage of the star_fine_tuning function
response = star_fine_tuning(
    model="bert",
    task="classification-text",
    sub_category="sentiment-analysis",
    media_id="abc123",
    description="Fine-tuning BERT for sentiment analysis",
    params={
        "num_train_epochs": 3,
        "per_device_train_batch_size": 16,
        "per_device_eval_batch_size": 32,
        "warmup_steps": 500,
        "weight_decay": 0.01,
        "logging_strategy": "epoch",
        "logging_steps": 100,
        "evaluation_strategy": "steps",
        "eval_steps": 200,
        "save_strategy": "no",
        "fp16": False,
        "load_best_model_at_end": True
    },
    params_input={},
    params_output="results.json",
    extension="json"
)
```

For more details on each parameter and their allowed values, refer to the documentation of the corresponding external service.

---
### fine_tuning_file_test

This endpoint tests the fine-tuned model using a file with the same structure as the training dataset and evaluates the model's efficiency.

**Parameters:**

- **model**: The fine-tuned model to be tested.
  - **Type**: `str`
  - **Description**: The identifier of the fine-tuned model to be evaluated.
- **test_file_id**: The file ID of the dataset to be used for testing.
  - **Type**: `str`
  - **Description**: The unique identifier of the test dataset uploaded previously.

**Example Usage:**

```python
test_results = client.fine_tuning.fine_tuning_file_test(
    model="fine_tuned_ROBIN_4",
    test_file_id="fileId"
)
print(test_results)
```

---

### fine_tuning_test

This endpoint tests the fine-tuned model using input parameters, allowing for specification of maximum tokens and temperature for response generation.

**Parameters:**

- **model**: The fine-tuned model to be tested.
  - **Type**: `str`
  - **Description**: The identifier of the fine-tuned model to be evaluated.
- **input_data**: Input parameters for testing.
  - **Type**: `list`
  - **Description**: A list of messages forming the input conversation for the model.
- **max_tokens**: Maximum number of tokens for the generated response.
  - **Type**: `int`
  - **Default**: `512`
  - **Description**: Specifies the maximum length of the response generated by the model.
- **temperature**: Controls the randomness of responses.
  - **Type**: `float`
  - **Default**: `1.0`
  - **Description**: A higher value results in more diverse responses.

**Example Usage:**

```python
response = client.fine_tuning.fine_tuning_test(
    model="fine_tuned_ROBIN_4",
    input_data=value,
    max_tokens=512,
    temperature=1.0
)
print(response.choices[0].delta.content, end="")
```

---

### get_fine_tuning_results

This endpoint retrieves the results of fine-tuning tasks that have been performed.

**Parameters:**

None.

**Example Usage:**

```python
results = client.fine_tuning.get_fine_tuning_results()
print(results)
```

---

### get_fine_tuning_detail

This endpoint provides detailed information about a specific fine-tuning task, including progress and test results.

**Parameters:**

- **task_id**: The unique identifier for the fine-tuning task.
  - **Type**: `str`
  - **Description**: The identifier of the fine-tuning task whose details are to be retrieved.

**Example Usage:**

```python
task_detail = client.fine_tuning.get_fine_tuning_detail(task_id="6488ea82-2688-4307-a4d7-fd97e0ac5b2a")
print(task_detail)
```

---
