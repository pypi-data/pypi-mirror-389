#!/bin/bash

# Setup script for GEMINI_API_KEY environment variable
API_KEY="AIzaSyAd2h4V8Fdgu91W7DnY-v6IP71kHZA7dh4"

echo "=================================================="
echo "Setting up GEMINI_API_KEY environment variable"
echo "=================================================="

# Detect shell
if [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
    SHELL_NAME="bash"
elif [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
    SHELL_NAME="zsh"
else
    SHELL_RC="$HOME/.profile"
    SHELL_NAME="sh"
fi

echo "Detected shell: $SHELL_NAME"
echo "Configuration file: $SHELL_RC"
echo ""

# Check if already exists
if grep -q "GEMINI_API_KEY" "$SHELL_RC"; then
    echo "⚠️  GEMINI_API_KEY already exists in $SHELL_RC"
    echo "To update it, edit the file manually:"
    echo "  nano $SHELL_RC"
else
    echo "Adding GEMINI_API_KEY to $SHELL_RC..."
    echo "" >> "$SHELL_RC"
    echo "# Gemini API Key" >> "$SHELL_RC"
    echo "export GEMINI_API_KEY=\"$API_KEY\"" >> "$SHELL_RC"
    echo "✅ Added successfully!"
fi

echo ""
echo "To activate in current session, run:"
echo "  source $SHELL_RC"
echo ""
echo "Or simply:"
echo "  export GEMINI_API_KEY=\"$API_KEY\""
echo ""
echo "To verify:"
echo "  echo \$GEMINI_API_KEY"
echo "=================================================="
