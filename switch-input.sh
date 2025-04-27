#!/bin/bash

INPUT="$1"

print_usage() {
    echo "Usage: $0 [INPUT]"
    echo ""
    echo "Available INPUT options:"
    echo "  usbc    → 0x1b"
    echo "  dp1     → 0x0f"
    echo "  dp2     → 0x13"
    echo "  hdmi1   → 0x11"
    echo "  hdmi2   → 0x12"
}

# Check if ddcutil exists
if ! command -v ddcutil >/dev/null 2>&1; then
    echo "Error: ddcutil not found. Please install ddcutil first."
    exit 2
fi

# Determine if we need sudo
if [ "$(id -u)" -eq 0 ]; then
    # Running as root
    DDCCTL="ddcutil"
else
    # Not running as root
    if command -v sudo >/dev/null 2>&1; then
        DDCCTL="sudo ddcutil"
    else
        echo "Error: Not running as root and sudo is not available."
        echo "Please run this script as root or install sudo."
        exit 2
    fi
fi

if [ -z "$INPUT" ]; then
    print_usage
    exit 1
fi

# Normalize input: lowercase and remove dashes
INPUT=$(echo "$INPUT" | tr '[:upper:]' '[:lower:]' | tr -d '-')

# Map input names to VCP values
case "$INPUT" in
    usbc)
        TARGET_HEX="0x1b"
        ;;
    dp1)
        TARGET_HEX="0x0f"
        ;;
    dp2)
        TARGET_HEX="0x13"
        ;;
    hdmi1)
        TARGET_HEX="0x11"
        ;;
    hdmi2)
        TARGET_HEX="0x12"
        ;;
    *)
        echo "Error: Unknown input '$INPUT'"
        echo ""
        print_usage
        exit 1
        ;;
esac

# Get current input setting
CURRENT_HEX=$($DDCCTL getvcp 60 --brief | awk '{print $4}' | sed 's/^x/0x/' | tr '[:upper:]' '[:lower:]')

if [ "$CURRENT_HEX" = "$TARGET_HEX" ]; then
    echo "Already on desired input: $INPUT ($TARGET_HEX)"
    exit 0
fi


# If different, perform the switch
echo "Switching input to $INPUT ($TARGET_HEX)..."
$DDCCTL setvcp 60 "$TARGET_HEX"
