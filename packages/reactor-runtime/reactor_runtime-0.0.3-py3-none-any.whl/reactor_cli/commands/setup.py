"""Setup command implementation.

Interactive setup for configuring Reactor weights management credentials.
This is for manual setup only - helps users configure their environment
variables for Supabase and AWS S3 access.
"""

import os

class SetupCommand:
    @staticmethod
    def register_subcommand(subparsers):
        """Register setup command"""
        setup_parser = subparsers.add_parser("setup", help="Check reactor weights configuration")
        setup_parser.set_defaults(func=SetupCommand)

    def __init__(self, args):
        """Initialize command with parsed arguments"""
        self.args = args

    def run(self):
        """Interactive setup for reactor weights"""
        print("Reactor weights setup")
        print("This will help you configure Supabase and AWS credentials")

        # Check current status
        supabase_vars = {
            "SUPABASE_URL": os.getenv("SUPABASE_URL"),
            "SUPABASE_SERVICE_KEY": os.getenv("SUPABASE_SERVICE_KEY"),
        }

        aws_vars = {
            "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
            "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY"),
        }

        # Setup Supabase
        print("\nSupabase setup:")
        print("Go to https://supabase.com/dashboard > Settings > API")

        supabase_url = input(f"Supabase URL (current: {supabase_vars['SUPABASE_URL'] or 'not set'}): ").strip()
        supabase_service_key = input(f"Supabase service key (current: {'***' if supabase_vars['SUPABASE_SERVICE_KEY'] else 'not set'}): ").strip()

        # Setup AWS
        print("\nAWS setup:")
        print("Go to AWS Console > IAM > Users (create user with S3 permissions)")

        aws_access_key = input(f"AWS Access Key ID (current: {'***' if aws_vars['AWS_ACCESS_KEY_ID'] else 'not set'}): ").strip()
        aws_secret_key = input(f"AWS Secret Key (current: {'***' if aws_vars['AWS_SECRET_ACCESS_KEY'] else 'not set'}): ").strip()

        # Generate export commands
        print("\nAdd these to your shell profile (.bashrc, .zshrc, etc.):")

        if supabase_url:
            print(f"export SUPABASE_URL='{supabase_url}'")
        if supabase_service_key:
            print(f"export SUPABASE_SERVICE_KEY='{supabase_service_key}'")
        if aws_access_key:
            print(f"export AWS_ACCESS_KEY_ID='{aws_access_key}'")
        if aws_secret_key:
            print(f"export AWS_SECRET_ACCESS_KEY='{aws_secret_key}'")

        print("\nRun 'source ~/.bashrc' (or restart terminal) to apply changes")

        # Test connections if user entered values
        if any([supabase_url, supabase_service_key, aws_access_key, aws_secret_key]):
            print("\nTesting connections with provided credentials...")
            self._test_connections(supabase_url, supabase_service_key, aws_access_key, aws_secret_key)

    def _test_connections(self, supabase_url=None, supabase_service_key=None, aws_access_key=None, aws_secret_key=None):
        """Test connections with provided credentials"""

        # Test Supabase with provided values or environment
        try:
            from supabase import create_client
            url = supabase_url or os.getenv('SUPABASE_URL')
            key = supabase_service_key or os.getenv('SUPABASE_SERVICE_KEY')

            if url and key:
                supabase = create_client(url, key)
                supabase.table('models').select('count').execute()
                print("Supabase: connection successful")
            else:
                print("Supabase: skipped (no credentials provided)")
        except Exception as e:
            print(f"Supabase: connection failed - {e}")

        # Test AWS with provided values or environment
        try:
            import boto3
            access_key = aws_access_key or os.getenv('AWS_ACCESS_KEY_ID')
            secret_key = aws_secret_key or os.getenv('AWS_SECRET_ACCESS_KEY')

            if access_key and secret_key:
                s3 = boto3.client('s3',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key)
                s3.list_buckets()
                print("AWS S3: connection successful")
            else:
                print("AWS S3: skipped (no credentials provided)")
        except Exception as e:
            print(f"AWS S3: connection failed - {e}")