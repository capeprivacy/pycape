<!-- markdownlint-disable -->

<a href="../pycape/cape.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `cape`
The Cape Python client. 

The Cape client uses websockets to connect to Cape enclaves that are hosting a user's deployed functions. Users must have gone through the process of developing a Cape function in Python and deploying it with the CLI, before being able to run it from the Cape client. 

Usage: 

:
``` 

     FUNCTION_ID = "9712r5dynf57l1rcns2"      cape = Cape(url="wss://enclave.capeprivacy.com")      cape.connect(FUNCTION_ID) 

     c1 = cape.invoke(3, 4, use_serdio=True)      print(c1)  # 5 

     c2 = cape.invoke(5, 12, use_serdio=True)      print(c2)  # 13 

     cape.close()  # release the websocket connection 



---

<a href="../pycape/cape.py#L51"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `Cape`
A websocket client for interacting with enclaves hosting Cape functions. 

This is the main interface for interacting with Cape functions from Python. See module documentation for usage example. 

<a href="../pycape/cape.py#L58"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `__init__`

```python
__init__(url='wss://enclave.capeprivacy.com', access_token=None, verbose=False)
```

Cape client constructor. 



**Args:**
 
 - <b>`url`</b>:  The Cape platform websocket URL, which is responsible for forwarding  client requests to the proper enclave instances. 
 - <b>`access_token`</b>:  Optional string containing a Cape access token generated  by the Cape CLI during `cape login`. If None, tries to load the access  token from a JSON at "$HOME/.config/cape/auth" (or OS-equivalent path). 
 - <b>`verbose`</b>:  Boolean controlling verbose logging for the "pycape" logger.  If True, sets log-level to DEBUG. 




---

<a href="../pycape/cape.py#L87"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `close`

```python
close()
```

Closes the enclave connection. 

---

<a href="../pycape/cape.py#L91"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `connect`

```python
connect(function_ref, function_token=None)
```

Connects to the enclave hosting the function denoted by `function_ref`. 

Note that this method creates a stateful websocket connection, which is a necessary precondition for callers of self.invoke. Care should be taken to close the websocket connection with self.close() once all invocations have finished. 



**Args:**
 
 - <b>`function_ref`</b>:  A function ID string or FunctionRef representing a deployed  Cape function. If a FunctionRef, can also include the function hash,  which  allows the user to verify that the enclave is hosting the same  function they deployed. 
 - <b>`function_token`</b>:  Optional string containing a Cape function token generated  by the Cape CLI during `cape token`. If None, the Cape access token  will be used instead. 



**Raises:**
 RuntimeError if the websocket response or the enclave attestation doc is  malformed, or if the enclave fails to return a function hash matching  our own. Exception if the enclave threw an error while trying to fulfill the  connection request. 

---

<a href="../pycape/cape.py#L118"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `invoke`

```python
invoke(*args, serde_hooks=None, use_serdio=False, **kwargs)
```

Invokes a function call from the currently connected websocket. 

This method assumes that the client is currently maintaining an open websocket connection to an enclave hosting a particular Cape function. Care should be taken to ensure that the function_red that spawned the connection is the correct one. The connection should be closed with self.close() once the caller is finished with their invocations. 



**Args:**
 
 - <b>`*args`</b>:  Arguments to pass to the connected Cape function. If  use_serdio=False, we expect a single argument of type `bytes`.  Otherwise, these arguments should match the positional arguments  of the undecorated Cape handler, and they will be auto-serialized by  serdio before being sent in the request. 
 - <b>`serde_hooks`</b>:  An optional pair of serdio encoder/decoder hooks convertible  to serdio.SerdeHookBundle. The hooks are necessary if the args / kwargs  have any custom (non-native) types that can't be handled by vanilla  msgpack. 
 - <b>`use_serdio`</b>:  Boolean controlling whether or not the inputs should be  auto-serialized by serdio. 
 - <b>`kwargs`</b>:  Keyword arguments to be passed to the connected Cape function.  These are treated the same way as the `args` are. 



**Returns:**
 If use_serdio=True, returns the auto-deserialized result of calling the connected Cape function on the given args/kwargs. If use_serdio=False, returns the output of the Cape function as raw bytes. 



**Raises:**
 RuntimeError if serialized inputs could not be HPKE-encrypted, or if  websocket response is malformed. 

---

<a href="../pycape/cape.py#L157"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `run`

```python
run(
    function_ref,
    *args,
    function_token=None,
    serde_hooks=None,
    use_serdio=False,
    **kwargs
)
```

Single-shot version of connect + invoke. 

This method takes care of establishing a websocket connection via self.connect, invoking it via self.invoke, and then finally closing the connection with self.close. `run` should be preferred when the caller doesn't need to invoke a Cape function more than once. 



**Args:**
 
 - <b>`function_ref`</b>:  A function ID string or FunctionRef representing a deployed  Cape function. If a FunctionRef, can also include the function hash,  which  allows the user to verify that the enclave is hosting the same  function they deployed. 
 - <b>`*args`</b>:  Arguments to pass to the connected Cape function. If  use_serdio=False, we expect a single argument of type `bytes`.  Otherwise, these arguments should match the positional arguments  of the undecorated Cape handler, and they will be auto-serialized by  serdio before being sent in the request. 
 - <b>`function_token`</b>:  Optional string containing a Cape function token generated  by the Cape CLI during `cape token`. If None, the Cape access token  will be used instead. 
 - <b>`serde_hooks`</b>:  An optional pair of serdio encoder/decoder hooks convertible  to serdio.SerdeHookBundle. The hooks are necessary if the args / kwargs  have any custom (non-native) types that can't be handled by vanilla  msgpack. 
 - <b>`use_serdio`</b>:  Boolean controlling whether or not the inputs should be  auto-serialized by serdio. 
 - <b>`kwargs`</b>:  Keyword arguments to be passed to the connected Cape function.  These are treated the same way as the `args` are. 



**Returns:**
 If use_serdio=True, returns the auto-deserialized result of calling the connected Cape function on the given args/kwargs. If use_serdio=False, returns the output of the Cape function as raw bytes. 



**Raises:**
 RuntimeError if serialized inputs could not be HPKE-encrypted, or if  websocket response is malformed. 


---

<a href="../pycape/cape.py#L342"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `FunctionAuthType`
An enumeration. 







---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
