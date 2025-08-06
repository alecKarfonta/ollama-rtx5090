#!/bin/bash

echo "🚀 Launching btop with GPU monitoring enabled!"
echo ""
echo "📊 GPU Monitoring Hotkeys:"
echo "  • Press '5' to show/hide GPU 1 (RTX 5090)"
echo "  • Press '6' to show/hide GPU 2 (if available)"
echo "  • Press '7' to show/hide GPU 3 (if available)"
echo "  • Press '0' to show/hide all GPU boxes"
echo ""
echo "🔧 Other useful keys:"
echo "  • Press 'h' for help"
echo "  • Press 'o' for options menu"  
echo "  • Press 'q' to quit"
echo ""
echo "🎯 Your RTX 5090 GPU usage should now be visible!"
echo "   Look for GPU utilization, power draw, and VRAM usage"
echo ""
sleep 2

# Launch btop with GPU support
/usr/local/bin/btop