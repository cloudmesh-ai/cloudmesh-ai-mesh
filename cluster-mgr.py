import argparse
import sys
from cloudmesh.ai.common.Shell import Shell
from cloudmesh.ai.common.io import console

def main():
    parser = argparse.ArgumentParser(description="CloudMesh-AI Cluster Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Deploy command
    subparsers.add_parser("deploy", help="Deploy the cluster configuration")

    # Status command
    subparsers.add_parser("status", help="Check the SLURM node status")

    # Manage command
    subparsers.add_parser("manage", help="Manage vLLM on the uva node")

    # Models command
    model_parser = subparsers.add_parser("models", help="Manage models on the nodes")
    model_parser.add_argument("action", choices=["download", "list", "delete"], help="Action to perform")
    model_parser.add_argument("node", help="Node to target (white, spark, both)")
    model_parser.add_argument("model_id", help="The HuggingFace model ID")

    # Logs command
    subparsers.add_parser("logs", help="Stream remote vLLM logs")

    args = parser.parse_args()

    if args.command == "deploy":
        Shell.run("python3 deploy_cluster.py")
    elif args.command == "status":
        Shell.run("python3 deploy/uva/status.py")
    elif args.command == "manage":
        Shell.run("python3 deploy/uva/manage_uva.py")
    elif args.command == "models":
        Shell.run(f"python3 models.py {args.action} {args.node} {args.model_id}")
    elif args.command == "logs":
        # Use Shell.live for logs to ensure real-time streaming
        Shell.live("python3 deploy/uva/stream_logs.py")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()