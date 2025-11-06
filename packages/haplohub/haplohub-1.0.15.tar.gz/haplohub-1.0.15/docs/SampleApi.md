# haplohub.SampleApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_sample**](SampleApi.md#create_sample) | **POST** /api/v1/cohort/{cohort_id}/sample/ | Create sample
[**delete_sample**](SampleApi.md#delete_sample) | **DELETE** /api/v1/cohort/{cohort_id}/sample/{sample_id}/ | Delete sample
[**get_sample**](SampleApi.md#get_sample) | **GET** /api/v1/cohort/{cohort_id}/sample/{sample_id}/ | Get sample
[**list_samples**](SampleApi.md#list_samples) | **GET** /api/v1/cohort/{cohort_id}/sample/ | List samples
[**update_sample**](SampleApi.md#update_sample) | **PUT** /api/v1/cohort/{cohort_id}/sample/{sample_id}/ | Update sample


# **create_sample**
> ResultResponseSampleSchema create_sample(cohort_id, create_sample_request)

Create sample

Create a new sample

### Example

* Bearer Authentication (Auth0JWTBearer):
```python
import time
import os
import haplohub
from haplohub.models.create_sample_request import CreateSampleRequest
from haplohub.models.result_response_sample_schema import ResultResponseSampleSchema
from haplohub.rest import ApiException
from pprint import pprint

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization: 
configuration = haplohub.Configuration(
    access_token=os.environ["API_KEY"]
)
# Enter a context with an instance of the API client
with haplohub.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = haplohub.SampleApi(api_client)
    cohort_id = haplohub.CohortId1() # CohortId1 | 
    create_sample_request = haplohub.CreateSampleRequest() # CreateSampleRequest | 

    try:
        # Create sample
        api_response = api_instance.create_sample(cohort_id, create_sample_request)
        print("The response of SampleApi->create_sample:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SampleApi->create_sample: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **cohort_id** | [**CohortId1**](.md)|  | 
 **create_sample_request** | [**CreateSampleRequest**](CreateSampleRequest.md)|  | 

### Return type

[**ResultResponseSampleSchema**](ResultResponseSampleSchema.md)

### Authorization

[Auth0JWTBearer](../README.md#Auth0JWTBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_sample**
> SuccessResponse delete_sample(cohort_id, sample_id)

Delete sample

Delete sample by its ID

### Example

* Bearer Authentication (Auth0JWTBearer):
```python
import time
import os
import haplohub
from haplohub.models.success_response import SuccessResponse
from haplohub.rest import ApiException
from pprint import pprint

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization: 
configuration = haplohub.Configuration(
    access_token=os.environ["API_KEY"]
)
# Enter a context with an instance of the API client
with haplohub.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = haplohub.SampleApi(api_client)
    cohort_id = haplohub.CohortId1() # CohortId1 | 
    sample_id = haplohub.SampleId1() # SampleId1 | 

    try:
        # Delete sample
        api_response = api_instance.delete_sample(cohort_id, sample_id)
        print("The response of SampleApi->delete_sample:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SampleApi->delete_sample: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **cohort_id** | [**CohortId1**](.md)|  | 
 **sample_id** | [**SampleId1**](.md)|  | 

### Return type

[**SuccessResponse**](SuccessResponse.md)

### Authorization

[Auth0JWTBearer](../README.md#Auth0JWTBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_sample**
> ResultResponseSampleSchema get_sample(cohort_id, sample_id)

Get sample

Get sample by its ID

### Example

* Bearer Authentication (Auth0JWTBearer):
```python
import time
import os
import haplohub
from haplohub.models.result_response_sample_schema import ResultResponseSampleSchema
from haplohub.rest import ApiException
from pprint import pprint

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization: 
configuration = haplohub.Configuration(
    access_token=os.environ["API_KEY"]
)
# Enter a context with an instance of the API client
with haplohub.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = haplohub.SampleApi(api_client)
    cohort_id = haplohub.CohortId1() # CohortId1 | 
    sample_id = haplohub.SampleId() # SampleId | 

    try:
        # Get sample
        api_response = api_instance.get_sample(cohort_id, sample_id)
        print("The response of SampleApi->get_sample:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SampleApi->get_sample: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **cohort_id** | [**CohortId1**](.md)|  | 
 **sample_id** | [**SampleId**](.md)|  | 

### Return type

[**ResultResponseSampleSchema**](ResultResponseSampleSchema.md)

### Authorization

[Auth0JWTBearer](../README.md#Auth0JWTBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_samples**
> PaginatedResponseSampleSchema list_samples(cohort_id)

List samples

List all samples

### Example

* Bearer Authentication (Auth0JWTBearer):
```python
import time
import os
import haplohub
from haplohub.models.paginated_response_sample_schema import PaginatedResponseSampleSchema
from haplohub.rest import ApiException
from pprint import pprint

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization: 
configuration = haplohub.Configuration(
    access_token=os.environ["API_KEY"]
)
# Enter a context with an instance of the API client
with haplohub.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = haplohub.SampleApi(api_client)
    cohort_id = haplohub.CohortId1() # CohortId1 | 

    try:
        # List samples
        api_response = api_instance.list_samples(cohort_id)
        print("The response of SampleApi->list_samples:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SampleApi->list_samples: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **cohort_id** | [**CohortId1**](.md)|  | 

### Return type

[**PaginatedResponseSampleSchema**](PaginatedResponseSampleSchema.md)

### Authorization

[Auth0JWTBearer](../README.md#Auth0JWTBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_sample**
> ResultResponseSampleSchema update_sample(cohort_id, sample_id, update_sample_request)

Update sample

Update sample by its ID

### Example

* Bearer Authentication (Auth0JWTBearer):
```python
import time
import os
import haplohub
from haplohub.models.result_response_sample_schema import ResultResponseSampleSchema
from haplohub.models.update_sample_request import UpdateSampleRequest
from haplohub.rest import ApiException
from pprint import pprint

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization: 
configuration = haplohub.Configuration(
    access_token=os.environ["API_KEY"]
)
# Enter a context with an instance of the API client
with haplohub.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = haplohub.SampleApi(api_client)
    cohort_id = haplohub.CohortId1() # CohortId1 | 
    sample_id = haplohub.SampleId1() # SampleId1 | 
    update_sample_request = haplohub.UpdateSampleRequest() # UpdateSampleRequest | 

    try:
        # Update sample
        api_response = api_instance.update_sample(cohort_id, sample_id, update_sample_request)
        print("The response of SampleApi->update_sample:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SampleApi->update_sample: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **cohort_id** | [**CohortId1**](.md)|  | 
 **sample_id** | [**SampleId1**](.md)|  | 
 **update_sample_request** | [**UpdateSampleRequest**](UpdateSampleRequest.md)|  | 

### Return type

[**ResultResponseSampleSchema**](ResultResponseSampleSchema.md)

### Authorization

[Auth0JWTBearer](../README.md#Auth0JWTBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

