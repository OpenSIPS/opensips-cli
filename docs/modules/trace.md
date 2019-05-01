# OpenSIPS CLI - Trace module

This module can be used by the `opensips-cli` tool to trace information about
calls passing through SIP. This module can offer information about SIP traffic
of a call, as well as other information such as script logs (logged using
`xlog`).

## Commands

This module does not export any command, but can receive a set of filters that
are used to filter the calls or traffic received from OpenSIPS. Available
filters for the current version are:
* `caller`: the identity of the caller, specified as `user` or `user@domain`;
this field is compared with the identity in the From header
* `callee`: the identity of the callee, specified as `user` or `user@domain`;
this field is compared with the identity in the Request URI
* `ip`: the IP where the call is initiated from

If there is no filter specified, when running the `trace` module, you will be
interactive prompted about what filter you want to apply.

**Note**: if you are not specifying any filters, you will receive the entire
traffic OpenSIPS is handling! Depending on your setup and traffic, this
connection might be overloaded.

## Examples

Trace the calls from *alice*:
```
opensips-cli -x trace caller=alice
```

Trace the calls from *alice* to *bob*:
```
opensips-cli -x trace caller=alice callee=bob
```

Trace the calls originated from IP 10.0.0.1:
```
opensips-cli -x trace ip=10.0.0.1
```

Call the `trace` module interactively without a filter:
```
(opensips-cli): trace
Caller filter: 
Callee filter: 
Source IP filter: 
No filter specified! Continue without a filter? [Y/n] (Default is n): y
```

## Limitations

Filtering limitations are coming from the filters that OpenSIPS `trace_start`
MI command supports. If one wants to define other filters, they will also need
to be implemented in OpenSIPS the `tracer`module.
