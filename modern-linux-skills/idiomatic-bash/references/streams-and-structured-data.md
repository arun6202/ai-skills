# Streams & structured data (cheat-sheet #5, modernized)

The cheat-sheet teaches stdin/stdout/stderr, pipes, and redirection. That model
is timeless. What's changed is that **modern CLIs emit structured data**, so a
pipeline should carry JSON, not whitespace-aligned text you parse with
`awk '{print $3}'` (brittle the moment a column wraps or a field is empty).

## Rule of thumb

1. Does the tool have a JSON/structured flag? Use it, pipe to `jq`.
2. If not, can `jc` parse its text into JSON? Use `jc`.
3. Only if neither, fall back to `awk`/`cut`/`grep` — and pin the field carefully.

## Native JSON from system tools

```bash
ip -j addr show            | jq -r '.[].addr_info[].local'
ss -O -H -tuln                                   # one row per socket (no wrap)
systemctl show nginx -p MainPID --value          # one property, machine-readable
journalctl -u nginx -o json | jq 'select(.PRIORITY<=3)'
docker inspect web         | jq -r '.[0].NetworkSettings.IPAddress'
lsblk --json               | jq -r '.blockdevices[].name'
findmnt --json /            | jq -r '.filesystems[0].source'
```

## `jc` — JSON-ify legacy tools that lack a flag

`jc` parses the text output of dozens of classic commands into JSON:

```bash
dig example.com      | jc --dig     | jq -r '.[0].answer[].data'
df -h                | jc --df      | jq -r '.[] | select(.use_percent>80)'
ps aux               | jc --ps      | jq -r '.[] | select(.cpu_percent>50).command'
ip route             | jc --ip-route| jq -r '.[].dst'
free -m              | jc --free    | jq '.[0].available'
```

Install via `pip install jc` or the distro package. It turns "scrape and pray"
into "select a field by name".

## `yq` for YAML/XML/TOML

```bash
yq '.services.web.image' docker-compose.yml      # YAML like jq
yq -p xml '.root.item' file.xml                  # XML → query
yq -p toml '.package.version' Cargo.toml
```

## Process substitution recap

Treat a command's output as a file, or feed a file to a command's input:

```bash
diff <(curl -s url-a) <(curl -s url-b)           # compare two live outputs
comm -13 <(sort old) <(sort new)                 # lines only in new
tee >(gzip > a.gz) >(sha256sum > a.sum) < big.bin >/dev/null   # fan-out
```

## The subshell trap (and the fix)

```bash
count=0
some_cmd | while read -r _; do ((count++)); done   # BUG: count is 0 after the loop
echo "$count"                                        # the pipe ran while in a subshell

count=0
while read -r _; do ((count++)); done < <(some_cmd)  # FIX: process substitution
echo "$count"                                        # correct
```

## When the data outgrows the pipe

If you're nesting `jq` three levels deep, joining datasets, or maintaining state
across lines, the pipeline has outgrown the shell. Move to Python (`json`,
`pandas`) or a real program. The shell's job is to *move* data between tools, not
to *be* the data layer.
