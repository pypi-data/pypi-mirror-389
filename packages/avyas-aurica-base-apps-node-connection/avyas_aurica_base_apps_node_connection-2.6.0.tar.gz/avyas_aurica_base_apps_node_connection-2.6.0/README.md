# Node Connection Manager

A service that manages node connections and provides visibility into both local and remote node status.

## Overview

The Node Connection Manager provides:
- **Local Node Status**: Status of the node where this instance is running
- **Execution Node Discovery**: Locate and connect to user's local execution node **from anywhere**
- **Remote Status Viewing**: Check your local execution node status from the cloud interface
- **Connection Management**: Maintain connections between cloud and local nodes
- **Remote Control**: Manage nodes remotely through API

## Key Feature: Remote Execution Node Status

When you access node-connection from **api.oneaurica.com**, you can now:
- ✅ See the API domain node status (current node)
- ✅ See YOUR local execution node status remotely
- ✅ Know if your local node is online/offline from anywhere
- ✅ Get your execution node's URL and uptime

**No more need to visit localhost!** The system uses the Digital Twin discovery service to find and check your execution node's status from the cloud.

## Important: Understanding Node Types

There are typically **two nodes** in the Aurica architecture:

1. **API Domain Node** (https://api.oneaurica.com)
   - Cloud-hosted server
   - Always running
   - Handles authentication and routing
   - Shows "Connected" because it's the cloud server

2. **Your Local Execution Node** (localhost:8000)
   - Runs on YOUR computer
   - Where your Digital Twin executes
   - Processes requests with your tools and data
   - May be offline when your computer is off

**When viewing node-connection on api.oneaurica.com**, you're seeing the API domain's status (which is why it shows "Connected").

**To see YOUR local node's status**, you need to:
- Access http://localhost:8000/node-connection/ while your local server is running
- Or use the Digital Twin discovery service to check your execution node status

## Features

- **Startup Authentication**: Automatically logs into API domain at startup
- **Connection Management**: Maintains connection details for authenticated users
- **Remote Control**: Manage and control nodes remotely through API
- **Health Monitoring**: Track node health and connection status
- **Auto-Reconnect**: Configurable automatic reconnection on connection loss

## API Endpoints

### Public Endpoints
- `GET /api/node/health` - Health check endpoint (no auth required)

### Protected Endpoints
- `GET /api/node/status` - Get current node connection status
- `GET /api/node/connection-details` - Get connection details for authenticated user
- `POST /api/node/reconnect` - Reconnect to API domain
- `PUT /api/node/config` - Update node configuration
- `POST /api/node/restart` - Restart this specific node's connection (resets connection state, does NOT restart server)

## Configuration

The node connection manager uses existing environment variables from the backend:

- **AUTH_SERVER_DOMAIN** - API domain for authentication (inherited from backend config)
- **AUTO_RECONNECT** - Enable/disable auto-reconnect (default: `true`)
- **HEARTBEAT_INTERVAL** - Heartbeat interval in seconds (default: `30`)
- **CONNECTION_TIMEOUT** - Connection timeout in seconds (default: `30`)

No additional environment variables are needed. The app leverages the existing JWT authentication system.

## Startup Behavior

On startup, the service:
1. Loads configuration from environment or config file
2. Authenticates with the API domain
3. Establishes connection and registers node
4. Starts heartbeat monitoring
5. Exposes connection details API for authenticated users

## Digital Twin Integration

The app provides tools for the Digital Twin to:
- Check node status
- Get connection details
- Trigger reconnection
- Update configuration
- Restart individual node connections (resets connection state only, server keeps running)

All operations respect the autonomy levels defined in the app configuration.

**Note**: The restart operation only resets the specific node's connection state and reconnects it. It does NOT restart the server process, making it safe for production use where multiple nodes may be running.
