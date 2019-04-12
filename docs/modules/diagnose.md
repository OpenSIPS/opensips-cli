# OpenSIPS CLI - Diagnose module

This module can be used in order to troubleshoot a given OpenSIPS instance.  By
using the MI interface and acting as an OpenSIPS event consumer via JSON-RPC,
it is able to offer, in a time-critical manner, valuable information regarding
commonly occurring emergencies in production, such as:

* excessive I/O operations (DNS, SQL, NoSQL) which are hogging OpenSIPS
* intensive CPU workloads (too much traffic / flood attacks)
* poorly sized shared or private memory pools
* slow DNS, SQL and NoSQL queries -- the tool answers the following:
	* which exact queries are being slow?
	* which are the the slowest queries?
	* which are the consistently slow queries?

## Configuration

No additional configuration is required by this module.  Its `diagnose load`
subcommand works best if the `psutil` Python package is present on the system.

## Examples

Quickly glance at a summarized status of an OpenSIPS instance:
```
opensips-cli -x diagnose
                         OpenSIPS Overview
                         -----------------
Worker Capacity: OK
Shared Memory:   CRITICAL (run 'diagnose memory' for more info)
Private Memory:  OK
SIP Processing:  CRITICAL (run 'diagnose sip' for more info)
DNS Queries:     CRITICAL (run 'diagnose dns' for more info)
SQL queries:     CRITICAL (run 'diagnose sql' for more info)
NoSQL Queries:   OK

					(press Ctrl-c to exit)
```

... ouch!  This OpenSIPS box has some issues, let's take them one by one.
First, let's take a look at the OpenSIPS UDP listeners, since these handle
the majority of our traffic:

```
opensips-cli -x diagnose load udp
                         OpenSIPS Processing Status

SIP UDP Interface #1 (udp:127.0.0.1:5060)
    Receive Queue: 0.0 bytes
    Avg. CPU usage: 0% (last 1 sec)

    Process  6 load:  0%,  0%,  0% (SIP receiver udp:127.0.0.1:5060)
    Process  7 load:  0%,  0%,  0% (SIP receiver udp:127.0.0.1:5060)
    Process  8 load:  0%,  0%,  0% (SIP receiver udp:127.0.0.1:5060)
    Process  9 load:  0%,  0%,  0% (SIP receiver udp:127.0.0.1:5060)
    Process 10 load:  0%,  0%,  0% (SIP receiver udp:127.0.0.1:5060)

    OK: no issues detected.
----------------------------------------------------------------------
SIP UDP Interface #2 (udp:10.0.0.10:5060)
    Receive Queue: 0.0 bytes
    Avg. CPU usage: 0% (last 1 sec)

    Process 11 load:  0%,  0%,  0% (SIP receiver udp:10.0.0.10:5060)
    Process 12 load:  0%,  0%,  0% (SIP receiver udp:10.0.0.10:5060)
    Process 13 load:  0%,  0%,  0% (SIP receiver udp:10.0.0.10:5060)

    OK: no issues detected.
----------------------------------------------------------------------

Info: the load percentages represent the amount of time spent by an
      OpenSIPS worker processing SIP messages, as opposed to waiting
      for new ones.  The three numbers represent the 'busy' percentage
      over the last 1 sec, last 1 min and last 10 min, respectively.

					(press Ctrl-c to exit)
```

The UDP listeners look fine, no real issues there.  Let's see what we can do
about the memory warning:

```
opensips-cli -x diagnose memory
Shared Memory Status
--------------------
    Current Usage: 27.5MB / 64.0MB (43%)
    Peak Usage: 64.0MB / 64.0MB (99%)

    CRITICAL: Peak shared memory usage > 90%, increase
              the "-m" command line parameter as soon as possible!!

Private Memory Status
---------------------
Each process has 16.0MB of private (packaged) memory.

    Process  1: no pkg memory stats found (MI FIFO)
    Process  2: no pkg memory stats found (HTTPD INADDR_ANY:8081)
    Process  3: no pkg memory stats found (JSON-RPC sender)
    Process  4: no pkg memory stats found (time_keeper)
    Process  5: no pkg memory stats found (timer)
    Process  6:  4% usage,  4% peak usage (SIP receiver udp:127.0.0.1:5060)
    Process  7:  4% usage,  4% peak usage (SIP receiver udp:127.0.0.1:5060)
    Process  8:  4% usage,  4% peak usage (SIP receiver udp:127.0.0.1:5060)
    Process  9:  4% usage,  4% peak usage (SIP receiver udp:127.0.0.1:5060)
    Process 10:  4% usage,  4% peak usage (SIP receiver udp:127.0.0.1:5060)
    Process 11:  4% usage,  4% peak usage (SIP receiver udp:10.0.0.10:5060)
    Process 12:  4% usage,  4% peak usage (SIP receiver udp:10.0.0.10:5060)
    Process 13:  4% usage,  4% peak usage (SIP receiver udp:10.0.0.10:5060)
    Process 14:  4% usage,  4% peak usage (SIP receiver hep_udp:10.0.0.10:9999)
    Process 15:  4% usage,  4% peak usage (SIP receiver hep_udp:10.0.0.10:9999)
    Process 16:  4% usage,  4% peak usage (SIP receiver hep_udp:10.0.0.10:9999)
    Process 17:  4% usage,  4% peak usage (TCP receiver)
    Process 18:  4% usage,  4% peak usage (Timer handler)
    Process 19:  4% usage,  4% peak usage (TCP main)

    OK: no issues detected.

					(press Ctrl-c to exit)
```

It seems the shared memory pool is too low, potentially causing problems during
peak traffic hours. We will bump it to 256 MB on the next restart.  Next, the
SIP traffic:

```
opensips-cli -x diagnose sip
In the last 2 seconds...
    SIP Processing [WARNING]
        * Slowest SIP messages:
            INVITE sip:sipp@localhost:5060, Call-ID: 59-26705@localhost (2191 us)
            INVITE sip:sipp@localhost:5060, Call-ID: 58-26705@localhost (2029 us)
            BYE sip:localhost:7050, Call-ID: 48-26705@localhost (1300 us)
        * 14 / 14 SIP messages (100%) exceeded threshold

					(press Ctrl-c to exit)
```

SIP message processing is a bit "slow" (below 1ms processing time).  Maybe
the current 1ms processing threshold is a bit excessive, we will bump it to
500 ms on this next restart.  Moving on to DNS queries:

```
opensips-cli -x diagnose dns
In the last 16 seconds...
    DNS Queries [WARNING]
        * Slowest queries:
            sipdomain.invalid (669 us)
            sipdomain.invalid (555 us)
            _sip._udp.sipdomain.invalid (541 us)
        * Constantly slow queries
            localhost (32 times exceeded threshold)
            sipdomain.invalid (2 times exceeded threshold)
            _sip._udp.sipdomain.invalid (1 times exceeded threshold)
        * 35 / 35 queries (100%) exceeded threshold

					(press Ctrl-c to exit)
```

We now know which are the slowest queries, and which are the ones failing
most often, so we can take action.  A similar output is provided for both
SQL and NoSQL queries:

```
opensips-cli -x diagnose sql
opensips-cli -x diagnose nosql
```

We apply the changes, restart OpenSIPS, and all errors are cleaned up!
Thank you, doctor!

```
opensips-cli -x diagnose
                         OpenSIPS Overview
                         -----------------
Worker Capacity: OK
Shared Memory:   OK
Private Memory:  OK
SIP Processing:  OK
DNS Queries:     OK
SQL queries:     OK
NoSQL Queries:   OK

					(press Ctrl-c to exit)
```
