"""Command-line interface for pysiphon."""

import click
import sys
from typing import Optional
from .client import SiphonClient
from .utils import bytes_to_hex


# Global client instance for interactive mode
_client: Optional[SiphonClient] = None


def get_client(host: str) -> SiphonClient:
    """Get or create client instance."""
    global _client
    if _client is None:
        _client = SiphonClient(host)
    return _client


@click.group(invoke_without_command=True)
@click.option('--host', default='localhost:50051', help='Server address')
@click.pass_context
def cli(ctx, host):
    """Python gRPC client for Siphon service."""
    ctx.ensure_object(dict)
    ctx.obj['host'] = host
    
    # If no subcommand, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.pass_context
def interactive(ctx):
    """Start interactive REPL mode."""
    host = ctx.obj['host']
    client = get_client(host)
    
    print(f"gRPC Siphon Client v0.1.0 (Python)")
    print(f"Connected to: {host}")
    print("\n=== Initialization Commands ===")
    print("  init <config_file>        - Load config and initialize all components")
    print("  status                    - Show server initialization status")
    print("  config <config_file>      - Load and send config to server")
    print("  init-memory               - Initialize memory subsystem")
    print("  init-input [window_name]  - Initialize input subsystem")
    print("  init-capture [window_name]- Initialize capture subsystem")
    print("\n=== Control Commands ===")
    print("  get <attribute>           - Get attribute value")
    print("  set <attribute> <type> <value> - Set attribute (int, float, array, bool)")
    print("  input <key1,key2,...> <hold_ms> <delay_ms> - Tap keys")
    print("  toggle <key> <0|1>        - Press/release key")
    print("  capture <filename>        - Capture frame to image file")
    print("  move <deltaX> <deltaY> <steps> - Move mouse")
    print("  exec <command> [args...]  - Execute command on server")
    print("\n=== Recording Commands ===")
    print("  rec-start <output_dir> <attr1,attr2,...> [max_duration_sec]")
    print("                            - Start recording (0 = unlimited duration)")
    print("  rec-stop <session_id>     - Stop recording session")
    print("  rec-status <session_id>   - Get recording status")
    print("  rec-download <session_id> <output_file>")
    print("                            - Download recording HDF5 file")
    print("\n=== General ===")
    print("  quit, exit                - Exit client")
    
    while True:
        try:
            command_line = input("\n> ").strip()
            if not command_line:
                continue
            
            parts = command_line.split()
            command = parts[0].lower()
            args = parts[1:]
            
            if command in ['quit', 'exit', 'q']:
                break
            
            elif command == 'init':
                if len(args) < 1:
                    print("Usage: init <config_file>")
                    continue
                
                config_file = args[0]
                print(f"Initializing from config: {config_file}")
                
                if client.init_all(config_file):
                    print("All subsystems initialized successfully!")
                else:
                    print("Initialization failed.")
            
            elif command == 'status':
                status = client.get_server_status()
                if status["success"]:
                    print("\n=== Server Status ===")
                    print(f"Config Set:          {'Yes' if status['config_set'] else 'No'}")
                    print(f"Memory Initialized:  {'Yes' if status['memory_initialized'] else 'No'}")
                    print(f"Input Initialized:   {'Yes' if status['input_initialized'] else 'No'}")
                    print(f"Capture Initialized: {'Yes' if status['capture_initialized'] else 'No'}")
                    if status['config_set']:
                        print(f"Process Name:        {status['process_name']}")
                        print(f"Window Name:         {status['window_name']}")
                        if status['process_id'] > 0:
                            print(f"Process ID:          {status['process_id']}")
                    print(f"Message: {status['message']}")
                else:
                    print("Failed to get server status")
            
            elif command == 'config':
                if len(args) < 1:
                    print("Usage: config <config_file>")
                    continue
                
                result = client.set_process_config(args[0])
                if result["success"]:
                    print(f"Config loaded - Process: {result['process_name']}, "
                          f"Window: {result['window_name']}, "
                          f"Attributes: {result['num_attributes']}")
                    print(result["message"])
                else:
                    print(f"Failed: {result['message']}")
            
            elif command == 'init-memory':
                result = client.initialize_memory()
                print(result["message"])
                if result["success"] and result["process_id"] > 0:
                    print(f"Process ID: {result['process_id']}")
            
            elif command == 'init-input':
                window_name = args[0] if args else ""
                result = client.initialize_input(window_name)
                print(result["message"])
            
            elif command == 'init-capture':
                window_name = args[0] if args else ""
                result = client.initialize_capture(window_name)
                print(result["message"])
                if result["success"]:
                    print(f"Window size: {result['window_width']}x{result['window_height']}")
            
            elif command == 'get':
                if len(args) < 1:
                    print("Usage: get <attribute>")
                    continue
                
                result = client.get_attribute(args[0])
                if result["success"]:
                    value = result["value"]
                    value_type = result["value_type"]
                    
                    if value_type == "array":
                        value = bytes_to_hex(value)
                    
                    print(f"{args[0]} = {value} ({value_type})")
                else:
                    print(f"Error: {result['message']}")
            
            elif command == 'set':
                if len(args) < 3:
                    print("Usage: set <attribute> <type> <value>")
                    continue
                
                attr_name = args[0]
                value_type = args[1]
                value_str = ' '.join(args[2:])
                
                # Convert value based on type
                if value_type == "int":
                    value = int(value_str)
                elif value_type == "float":
                    value = float(value_str)
                elif value_type == "bool":
                    value = bool(int(value_str))
                elif value_type == "array":
                    value = value_str  # Will be converted in set_attribute
                else:
                    print(f"Unknown type: {value_type}")
                    continue
                
                result = client.set_attribute(attr_name, value, value_type)
                print(result["message"])
            
            elif command == 'input':
                if len(args) < 3:
                    print("Usage: input <key1,key2,...> <hold_ms> <delay_ms>")
                    continue
                
                keys = args[0].split(',')
                hold_ms = int(args[1])
                delay_ms = int(args[2])
                
                result = client.input_key_tap(keys, hold_ms, delay_ms)
                if result["success"]:
                    print(f"Keys {','.join(keys)} inputted successfully")
                else:
                    print(f"Failed: {result['message']}")
            
            elif command == 'toggle':
                if len(args) < 2:
                    print("Usage: toggle <key> <0|1>")
                    continue
                
                key = args[0]
                toggle = bool(int(args[1]))
                
                result = client.input_key_toggle(key, toggle)
                if result["success"]:
                    print(f"Key {key} {'pressed' if toggle else 'released'}")
                else:
                    print(f"Failed: {result['message']}")
            
            elif command == 'capture':
                if len(args) < 1:
                    print("Usage: capture <filename>")
                    continue
                
                filename = args[0]
                if client.capture_and_save(filename):
                    print(f"Frame saved to: {filename}")
                else:
                    print("Failed to capture frame")
            
            elif command == 'move':
                if len(args) < 3:
                    print("Usage: move <deltaX> <deltaY> <steps>")
                    continue
                
                delta_x = int(args[0])
                delta_y = int(args[1])
                steps = int(args[2])
                
                result = client.move_mouse(delta_x, delta_y, steps)
                if result["success"]:
                    print("Mouse moved successfully")
                else:
                    print(f"Failed: {result['message']}")
            
            elif command == 'exec':
                if len(args) < 1:
                    print("Usage: exec <command> [args...]")
                    continue
                
                cmd = args[0]
                cmd_args = args[1:]
                
                print(f"Executing: {cmd} {' '.join(cmd_args)}")
                result = client.execute_command(cmd, cmd_args)
                
                print(f"Success: {result['success']}")
                print(f"Exit Code: {result['exit_code']}")
                print(f"Execution Time: {result['execution_time_ms']}ms")
                print(f"Message: {result['message']}")
                
                if result['stdout']:
                    print("Output:")
                    print(result['stdout'])
                
                if result['stderr']:
                    print("Error Output:")
                    print(result['stderr'])
            
            elif command == 'rec-start':
                if len(args) < 2:
                    print("Usage: rec-start <output_dir> <attr1,attr2,...> [max_duration_sec]")
                    continue
                
                output_dir = args[0]
                attributes = args[1].split(',')
                max_duration = int(args[2]) if len(args) > 2 else 0
                
                print(f"Starting recording...")
                print(f"  Output directory: {output_dir}")
                print(f"  Attributes: {', '.join(attributes)}")
                print(f"  Max duration: {'unlimited' if max_duration == 0 else f'{max_duration}s'}")
                
                result = client.start_recording(attributes, output_dir, max_duration)
                
                if result["success"]:
                    print(f"\n=== Recording Started! ===")
                    print(f"Session ID: {result['session_id']}")
                    print(f"Message: {result['message']}")
                    print(f"\nUse 'rec-status {result['session_id']}' to check status")
                    print(f"Use 'rec-stop {result['session_id']}' to stop recording")
                else:
                    print(f"Failed: {result['message']}")
            
            elif command == 'rec-stop':
                if len(args) < 1:
                    print("Usage: rec-stop <session_id>")
                    continue
                
                session_id = args[0]
                print(f"Stopping recording: {session_id}")
                
                result = client.stop_recording(session_id)
                
                if result["success"]:
                    print(f"\n=== Recording Stopped! ===")
                    print(f"Total Frames: {result['total_frames']}")
                    print(f"Dropped Frames: {result['dropped_frames']}")
                    print(f"Average Latency: {result['average_latency_ms']:.2f}ms")
                    print(f"Duration: {result['actual_duration_seconds']:.1f}s")
                    print(f"Actual FPS: {result['actual_fps']:.1f}")
                    print(f"Message: {result['message']}")
                    
                    if result['actual_fps'] < 55.0:
                        print(f"\n  WARNING: Recording FPS ({result['actual_fps']:.1f}) is below target 60fps!")
                else:
                    print(f"Failed: {result['message']}")
            
            elif command == 'rec-status':
                if len(args) < 1:
                    print("Usage: rec-status <session_id>")
                    continue
                
                session_id = args[0]
                result = client.get_recording_status(session_id)
                
                if result["success"]:
                    print(f"\n=== Recording Status ===")
                    print(f"Session ID: {session_id}")
                    print(f"Status: {'RECORDING' if result['is_recording'] else 'STOPPED'}")
                    
                    if result['is_recording']:
                        print(f"Current Frame: {result['current_frame']}")
                        print(f"Elapsed Time: {result['elapsed_time_seconds']:.1f}s")
                        print(f"Current Latency: {result['current_latency_ms']:.2f}ms")
                        print(f"Dropped Frames: {result['dropped_frames']}")
                        
                        if result['current_latency_ms'] <= 16.67:
                            print("Performance: GOOD (within 60fps budget)")
                        else:
                            print("Performance: WARNING (exceeding 60fps budget)")
                        
                        if result['elapsed_time_seconds'] > 0:
                            fps = result['current_frame'] / result['elapsed_time_seconds']
                            print(f"Average FPS: {fps:.1f}")
                else:
                    print(f"Failed: {result['message']}")
            
            elif command == 'rec-download':
                if len(args) < 2:
                    print("Usage: rec-download <session_id> <output_file>")
                    continue
                
                session_id = args[0]
                output_file = args[1]
                
                print(f"Downloading recording: {session_id}")
                print(f"Output file: {output_file}")
                
                if client.download_recording(session_id, output_file):
                    print("Download successful!")
                else:
                    print("Download failed!")
            
            else:
                print(f"Unknown command: {command}")
                print("Type 'quit' to exit")
        
        except KeyboardInterrupt:
            print("\nUse 'quit' to exit")
        except EOFError:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("\nGoodbye!")


# Single-command mode subcommands

@cli.command()
@click.argument('config_file')
@click.pass_context
def init(ctx, config_file):
    """Initialize all subsystems from config file."""
    client = get_client(ctx.obj['host'])
    if client.init_all(config_file):
        click.echo("Initialization complete!")
        sys.exit(0)
    else:
        click.echo("Initialization failed!")
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Show server status."""
    client = get_client(ctx.obj['host'])
    result = client.get_server_status()
    
    if result["success"]:
        click.echo("\n=== Server Status ===")
        click.echo(f"Config Set:          {'Yes' if result['config_set'] else 'No'}")
        click.echo(f"Memory Initialized:  {'Yes' if result['memory_initialized'] else 'No'}")
        click.echo(f"Input Initialized:   {'Yes' if result['input_initialized'] else 'No'}")
        click.echo(f"Capture Initialized: {'Yes' if result['capture_initialized'] else 'No'}")
        if result['config_set']:
            click.echo(f"Process Name:        {result['process_name']}")
            click.echo(f"Window Name:         {result['window_name']}")
            if result['process_id'] > 0:
                click.echo(f"Process ID:          {result['process_id']}")
        click.echo(f"Message: {result['message']}")
    else:
        click.echo("Failed to get server status")
        sys.exit(1)


@cli.command()
@click.argument('attribute')
@click.pass_context
def get(ctx, attribute):
    """Get attribute value."""
    client = get_client(ctx.obj['host'])
    result = client.get_attribute(attribute)
    
    if result["success"]:
        value = result["value"]
        if result["value_type"] == "array":
            value = bytes_to_hex(value)
        click.echo(f"{attribute} = {value} ({result['value_type']})")
    else:
        click.echo(f"Error: {result['message']}")
        sys.exit(1)


@cli.command()
@click.argument('attribute')
@click.argument('value_type')
@click.argument('value')
@click.pass_context
def set(ctx, attribute, value_type, value):
    """Set attribute value."""
    client = get_client(ctx.obj['host'])
    
    # Convert value based on type
    if value_type == "int":
        converted_value = int(value)
    elif value_type == "float":
        converted_value = float(value)
    elif value_type == "bool":
        converted_value = bool(int(value))
    elif value_type == "array":
        converted_value = value  # Will be converted in set_attribute
    else:
        click.echo(f"Unknown type: {value_type}")
        sys.exit(1)
    
    result = client.set_attribute(attribute, converted_value, value_type)
    click.echo(result["message"])
    
    if not result["success"]:
        sys.exit(1)


@cli.command()
@click.argument('keys')
@click.argument('hold_ms', type=int)
@click.argument('delay_ms', type=int)
@click.pass_context
def input(ctx, keys, hold_ms, delay_ms):
    """Tap keys (comma-separated)."""
    client = get_client(ctx.obj['host'])
    key_list = keys.split(',')
    
    result = client.input_key_tap(key_list, hold_ms, delay_ms)
    if result["success"]:
        click.echo(f"Keys {keys} inputted successfully")
    else:
        click.echo(f"Failed: {result['message']}")
        sys.exit(1)


@cli.command()
@click.argument('key')
@click.argument('state', type=int)
@click.pass_context
def toggle(ctx, key, state):
    """Toggle key state (1=press, 0=release)."""
    client = get_client(ctx.obj['host'])
    toggle_state = bool(state)
    
    result = client.input_key_toggle(key, toggle_state)
    if result["success"]:
        click.echo(f"Key {key} {'pressed' if toggle_state else 'released'}")
    else:
        click.echo(f"Failed: {result['message']}")
        sys.exit(1)


@cli.command()
@click.argument('filename')
@click.pass_context
def capture(ctx, filename):
    """Capture frame to image file."""
    client = get_client(ctx.obj['host'])
    
    if client.capture_and_save(filename):
        click.echo(f"Frame saved to: {filename}")
    else:
        click.echo("Failed to capture frame")
        sys.exit(1)


@cli.command()
@click.argument('delta_x', type=int)
@click.argument('delta_y', type=int)
@click.argument('steps', type=int)
@click.pass_context
def move(ctx, delta_x, delta_y, steps):
    """Move mouse by delta."""
    client = get_client(ctx.obj['host'])
    
    result = client.move_mouse(delta_x, delta_y, steps)
    if result["success"]:
        click.echo("Mouse moved successfully")
    else:
        click.echo(f"Failed: {result['message']}")
        sys.exit(1)


@cli.command()
@click.argument('command')
@click.argument('args', nargs=-1)
@click.pass_context
def exec(ctx, command, args):
    """Execute command on server."""
    client = get_client(ctx.obj['host'])
    
    result = client.execute_command(command, list(args))
    
    click.echo(f"Success: {result['success']}")
    click.echo(f"Exit Code: {result['exit_code']}")
    click.echo(f"Execution Time: {result['execution_time_ms']}ms")
    
    if result['stdout']:
        click.echo("Output:")
        click.echo(result['stdout'])
    
    if result['stderr']:
        click.echo("Error Output:")
        click.echo(result['stderr'])
    
    if not result["success"]:
        sys.exit(1)


@cli.command('rec-start')
@click.argument('output_dir')
@click.argument('attributes')
@click.argument('max_duration', type=int, default=0, required=False)
@click.pass_context
def rec_start(ctx, output_dir, attributes, max_duration):
    """Start recording session."""
    client = get_client(ctx.obj['host'])
    attr_list = attributes.split(',')
    
    result = client.start_recording(attr_list, output_dir, max_duration)
    
    if result["success"]:
        click.echo(f"Recording started!")
        click.echo(f"Session ID: {result['session_id']}")
        click.echo(f"Message: {result['message']}")
    else:
        click.echo(f"Failed: {result['message']}")
        sys.exit(1)


@cli.command('rec-stop')
@click.argument('session_id')
@click.pass_context
def rec_stop(ctx, session_id):
    """Stop recording session."""
    client = get_client(ctx.obj['host'])
    
    result = client.stop_recording(session_id)
    
    if result["success"]:
        click.echo(f"Recording stopped!")
        click.echo(f"Total Frames: {result['total_frames']}")
        click.echo(f"Dropped Frames: {result['dropped_frames']}")
        click.echo(f"Average Latency: {result['average_latency_ms']:.2f}ms")
        click.echo(f"Duration: {result['actual_duration_seconds']:.1f}s")
        click.echo(f"Actual FPS: {result['actual_fps']:.1f}")
    else:
        click.echo(f"Failed: {result['message']}")
        sys.exit(1)


@cli.command('rec-status')
@click.argument('session_id')
@click.pass_context
def rec_status(ctx, session_id):
    """Get recording session status."""
    client = get_client(ctx.obj['host'])
    
    result = client.get_recording_status(session_id)
    
    if result["success"]:
        click.echo(f"\n=== Recording Status ===")
        click.echo(f"Status: {'RECORDING' if result['is_recording'] else 'STOPPED'}")
        
        if result['is_recording']:
            click.echo(f"Current Frame: {result['current_frame']}")
            click.echo(f"Elapsed Time: {result['elapsed_time_seconds']:.1f}s")
            click.echo(f"Current Latency: {result['current_latency_ms']:.2f}ms")
            click.echo(f"Dropped Frames: {result['dropped_frames']}")
    else:
        click.echo(f"Failed: {result['message']}")
        sys.exit(1)


@cli.command('rec-download')
@click.argument('session_id')
@click.argument('output_file')
@click.pass_context
def rec_download(ctx, session_id, output_file):
    """Download recording file."""
    client = get_client(ctx.obj['host'])
    
    if client.download_recording(session_id, output_file):
        click.echo("Download successful!")
    else:
        click.echo("Download failed!")
        sys.exit(1)


if __name__ == '__main__':
    cli(obj={})

