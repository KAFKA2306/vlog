# systemd

Target location for `vlog.service`, daily services/timers, failure units, and installation helpers.

Root-level units remain active during the behavior-preserving migration gate. They move here only with updated install scripts, Taskfile commands, path sandboxing, and `systemd-analyze verify` evidence.
