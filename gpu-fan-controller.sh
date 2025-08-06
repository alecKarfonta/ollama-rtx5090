#!/bin/bash

# GPU-Chassis Fan Controller
# Automatically adjusts chassis fan speed based on GPU temperature and fan speed

# Configuration
GPU_TEMP_THRESHOLD=70          # Temperature threshold in Celsius
MAX_CHASSIS_FAN_SPEED=255      # Maximum PWM value (100%)
MIN_CHASSIS_FAN_SPEED=77       # Minimum PWM value (~30%)
HWMON_PATH="/sys/class/hwmon/hwmon4"
CHECK_INTERVAL=5               # Check every 5 seconds

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to set chassis fan speed
set_chassis_fans() {
    local speed=$1
    local mode=$2  # 1 for manual, 5 for auto
    
    for i in {1..7}; do
        echo $mode > "${HWMON_PATH}/pwm${i}_enable" 2>/dev/null
        echo $speed > "${HWMON_PATH}/pwm${i}" 2>/dev/null
    done
}

# Function to get current chassis fan speeds
get_chassis_fan_speeds() {
    local speeds=()
    for i in {1..7}; do
        local fan_speed=$(cat "${HWMON_PATH}/fan${i}_input" 2>/dev/null)
        if [[ "$fan_speed" != "0" && -n "$fan_speed" ]]; then
            speeds+=("Fan${i}: ${fan_speed}rpm")
        fi
    done
    echo "${speeds[@]}"
}

# Function to calculate scaled fan speed based on GPU metrics
calculate_fan_speed() {
    local gpu_temp=$1
    local gpu_fan=$2
    
    if [[ $gpu_temp -ge $GPU_TEMP_THRESHOLD ]]; then
        echo $MAX_CHASSIS_FAN_SPEED  # Max speed when over threshold
    elif [[ $gpu_temp -ge 60 ]]; then
        # Scale between 75-100% for temps 60-69°C
        local scale_factor=$(( (gpu_temp - 60) * 25 / 10 + 75 ))
        echo $(( scale_factor * 255 / 100 ))
    elif [[ $gpu_temp -ge 50 ]]; then
        # Scale between 50-75% for temps 50-59°C
        local scale_factor=$(( (gpu_temp - 50) * 25 / 10 + 50 ))
        echo $(( scale_factor * 255 / 100 ))
    else
        # Use GPU fan speed as reference for temps under 50°C
        echo $(( gpu_fan * 255 / 100 ))
    fi
}

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Restoring automatic fan control...${NC}"
    set_chassis_fans 0 5  # Return to auto mode
    echo -e "${GREEN}Fan control restored to automatic mode${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}This script needs to run with sudo to control fans${NC}"
    echo "Usage: sudo $0"
    exit 1
fi

# Check if hwmon path exists
if [[ ! -d "$HWMON_PATH" ]]; then
    echo -e "${RED}Hardware monitor path not found: $HWMON_PATH${NC}"
    echo "Make sure the nct6775 driver is loaded: sudo modprobe nct6775"
    exit 1
fi

echo -e "${GREEN}🌪️  GPU-Chassis Fan Controller Started${NC}"
echo -e "${BLUE}GPU Temperature Threshold: ${GPU_TEMP_THRESHOLD}°C${NC}"
echo -e "${BLUE}Check Interval: ${CHECK_INTERVAL} seconds${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop and restore automatic fan control${NC}"
echo ""

# Main monitoring loop
while true; do
    # Get GPU metrics (temp, fan_speed, power, mem_used, mem_total)
    GPU_DATA=$(nvidia-smi --query-gpu=temperature.gpu,fan.speed,power.draw,memory.used,memory.total --format=csv,noheader,nounits)
    
    if [[ -z "$GPU_DATA" ]]; then
        echo -e "${RED}Failed to get GPU data from nvidia-smi${NC}"
        sleep $CHECK_INTERVAL
        continue
    fi
    
    # Parse GPU data
    IFS=',' read -r GPU_TEMP GPU_FAN_SPEED POWER_DRAW MEM_USED MEM_TOTAL <<< "$GPU_DATA"
    
    # Remove spaces
    GPU_TEMP=$(echo $GPU_TEMP | tr -d ' ')
    GPU_FAN_SPEED=$(echo $GPU_FAN_SPEED | tr -d ' ')
    POWER_DRAW=$(echo $POWER_DRAW | tr -d ' ')
    MEM_USED=$(echo $MEM_USED | tr -d ' ')
    
    # Calculate appropriate chassis fan speed
    CHASSIS_PWM=$(calculate_fan_speed $GPU_TEMP $GPU_FAN_SPEED)
    CHASSIS_PERCENT=$(( CHASSIS_PWM * 100 / 255 ))
    
    # Set chassis fan speed
    set_chassis_fans $CHASSIS_PWM 1
    
    # Get current chassis fan speeds for display
    CHASSIS_SPEEDS=$(get_chassis_fan_speeds)
    
    # Determine temperature color
    if [[ $GPU_TEMP -ge $GPU_TEMP_THRESHOLD ]]; then
        TEMP_COLOR=$RED
        STATUS="🔥 HIGH TEMP - MAX FANS"
    elif [[ $GPU_TEMP -ge 60 ]]; then
        TEMP_COLOR=$YELLOW
        STATUS="⚠️  ELEVATED TEMP"
    else
        TEMP_COLOR=$GREEN
        STATUS="✅ NORMAL TEMP"
    fi
    
    # Display current status
    echo -e "${BLUE}$(date '+%H:%M:%S')${NC} | GPU: ${TEMP_COLOR}${GPU_TEMP}°C${NC} ${GPU_FAN_SPEED}% | Power: ${POWER_DRAW}W | Chassis: ${CHASSIS_PERCENT}% | $STATUS"
    echo -e "  └─ $CHASSIS_SPEEDS"
    
    sleep $CHECK_INTERVAL
done