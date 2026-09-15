# Cloudmesh AI Mesh - New Features

## SSH Tunnel Command

Added support for creating and managing SSH tunnels to remote hosts in the mesh configuration.

### Command Usage

```bash
cmc mesh tunnel <action> [<host>]
```

Where:
- `<action>` is one of: `start`, `stop`, or `status`
- `<host>` (optional) is a hostname defined in config.yaml

### Enhanced Features

The command now supports multiple actions:
1. **Start**: Create SSH tunnels for specific hosts or all SSH-enabled hosts
2. **Stop**: Terminate SSH tunnels for specific hosts or all active tunnels  
3. **Status**: Check the status of specific tunnels or all active tunnels

### Examples

```bash
# Start tunnel for specific host
cmc mesh tunnel start white

# Start tunnels for all SSH-enabled hosts
cmc mesh tunnel start

# Stop tunnel for specific host
cmc mesh tunnel stop spark

# Stop all active tunnels
cmc mesh tunnel stop

# Check status of all tunnels
cmc mesh tunnel status
```

### Configuration Requirements

The host must be defined in `src/cloudmesh/ai/mesh/config.yaml` with:

1. `ssh: true` to enable SSH tunneling
2. A `port` section with both `local` and `remote` ports defined

Example configuration:
```yaml
white:
  server: olama
  model: qwen2.5-coder:14b
  ssh: true
  system:
    name: "rtx-3090"
    cpu: "AMD Ryzen 9 5950X 16-Core Processor"
    cpu_mem: "128 GiB"
    gpu: "NVIDIA Corporation GA102 [GeForce RTX 3090] (rev a1)"
    gpu_mem: "24.0 GiB"
  port: 
    remote: 11434
    local: 10005
```

### Features

- **Multiple Actions**: Start, stop, and check status of SSH tunnels
- **Host Selection**: Operate on specific hosts or all SSH-enabled hosts
- **Configuration Integration**: Uses existing port mappings from config.yaml
- **Status Management**: Provides detailed status information for active tunnels
- **Error Handling**: Comprehensive error handling for connection failures, configuration issues, etc.

### Implementation Details

The implementation includes:
1. `TunnelManager` class in `src/cloudmesh/ai/mesh/tunnel_manager.py`
2. `Tunnel` class in `src/cloudmesh/ai/common/ssh/tunnel.py` 
3. Enhanced CLI command registration in `src/cloudmesh/ai/command/mesh.py`

### Security Considerations

- Uses SSH's built-in host key checking (disabled for automation via flags)
- Tunnels are created with background SSH processes
- Supports graceful shutdown of tunnel processes

## Set Command

Added support for setting local ports to match remote ports:

```bash
cmc mesh set <host>
```

This command sets the local port for a host to match its configured remote port value.

## Enhanced Info Command

The `cmc mesh info` command has been enhanced to display port configuration information for all hosts in the mesh, including:
- Local and remote port mappings
- SSH status for each host
- Server type for each host