### requestr
A wrapper library for requests, optimised for JSON and HTML

Installation:
`pip install requestr`

```
import requestr

url = 'https://jsonplaceholder.typicode.com/posts/1'

response = requestr.get(url)
>>> response.data
{
  'userId': 1,
  'id': 1,
  'title': 'sunt aut facere repellat provident occaecati excepturi optio reprehenderit',
  'body': 'quia et suscipit...'
}
>>> response.data.title
'sunt aut facere repellat provident occaecati excepturi optio reprehenderit'
```

```
import requestr

url = 'https://example.com'

response = requestr.get(url)

h1_tag = response.soup.select_one('h1')
>>> h1_tag.text
'Example domain'
```

```
from requestr import Session

session = Session()

url = 'https://jsonplaceholder.typicode.com/posts/1'

response = session.get(url)
>>> response.data
{
  'userId': 1,
  'id': 1,
  'title': 'sunt aut facere repellat provident occaecati excepturi optio reprehenderit',
  'body': 'quia et suscipit...'
}
>>> response.data.id
1
```

```
from requestr import requestr_futures
from time import sleep

url = 'https://jsonplaceholder.typicode.com/posts/1'

future = requestr_futures.get(url) # Request is executed in background thread without blocking code execution
sleep(3)
response = future.result()
>>> response.data
{
  'userId': 1,
  'id': 1,
  'title': 'sunt aut facere repellat provident occaecati excepturi optio reprehenderit',
  'body': 'quia et suscipit...'
}
>>> response.data.title
'sunt aut facere repellat provident occaecati excepturi optio reprehenderit'
```

```
from requestr import FuturesSession
from time import sleep

session = FuturesSession()

url = 'https://jsonplaceholder.typicode.com/posts/1'

response = session.get(url) # Request is executed in background thread without blocking code execution
sleep(3)
response = future.result()
>>> response.data
{
  'userId': 1,
  'id': 1,
  'title': 'sunt aut facere repellat provident occaecati excepturi optio reprehenderit',
  'body': 'quia et suscipit...'
}
>>> response.data.id
1
```