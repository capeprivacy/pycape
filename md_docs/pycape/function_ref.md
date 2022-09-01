<!-- markdownlint-disable -->

<a href="../../pycape/function_ref.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

# <kbd>module</kbd> `function_ref`
A structured representation of a deployed Cape function. 

A FunctionRef is intended to capture any/all metadata related to a Cape function. It is generally created from user-supplied metadata, which is given to the user as output of the Cape CLI's `deploy` command. 

Usage: 

```
fid = "asdf231lkg1324afdg"
fhash = str(b"2l1h21jhgb2k1jh3".hex())
fref = FunctionRef(fid, fhash)

cape = Cape()
cape.connect(fref)
``` 



---

<a href="../../pycape/function_ref.py#L22"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `FunctionAuthType`
Enum representing the auth type for a function. 

The auth type determines how :class:`.Cape` will supply authentication info for requests involving a particular function. 





---

<a href="../../pycape/function_ref.py#L33"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `FunctionRef`
A structured reference to a Cape function. 

<a href="../../pycape/function_ref.py#L36"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `__init__`

```python
__init__(id: str, hash: Optional[str] = None, token: Optional[str] = None)
```

Instantiate a FunctionRef. 



**Args:**
 
 - <b>`id`</b>:  Required string denoting the function ID of the deployed Cape  function. This is typically given in the output of the Cape CLI's  `deploy` command. 
 - <b>`hash`</b>:  Optional string denoting the function hash of the deployed  Cape function. If supplied, the Cape client will attempt to verify that  enclave responses include a matching function hash whenever this 
 - <b>`:class`</b>: `~.FunctionRef` is included in Cape requests. 
 - <b>`token`</b>:  Optional string containing a Cape function token generated  by the Cape CLI during `cape token`. If None, the Cape access token 
 - <b>`provided to `</b>: class:`.Cape` will be used by :meth:`.Cape.connect` / 
 - <b>`:meth`</b>: `.Cape.run` instead. 


---

#### <kbd>property</kbd> auth_protocol





---

#### <kbd>property</kbd> auth_type





---

#### <kbd>property</kbd> hash





---

#### <kbd>property</kbd> id





---

#### <kbd>property</kbd> token







---

<a href="../../pycape/function_ref.py#L89"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `set_auth_type`

```python
set_auth_type(auth_type: FunctionAuthType)
```








---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
