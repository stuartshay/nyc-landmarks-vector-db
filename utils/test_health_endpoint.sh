#!/bin/bash

# Test Health Endpoint Script
# Tests the health endpoints for the NYC Landmarks Vector DB service
# Also provides debugging information for monitoring infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}NYC Landmarks Vector DB - Health Endpoint Test${NC}"
echo "=============================================="
echo

# Function to print status messages
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Test endpoints
PUBLIC_ENDPOINT="https://vector-db.coredatastore.com/health"
CLOUD_RUN_ENDPOINT="https://nyc-landmarks-vector-db-1052843754581.us-east4.run.app/health"
PROJECT_ID="velvety-byway-327718"

test_count=0
pass_count=0

# Command line options
VERBOSE=false
DEBUG_MONITORING=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -d|--debug)
            DEBUG_MONITORING=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -v, --verbose       Show detailed output"
            echo "  -d, --debug         Show monitoring debug information"
            echo "  -h, --help          Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to test an endpoint
test_endpoint() {
    local url="$1"
    local name="$2"

    echo "Testing $name endpoint: $url"
    test_count=$((test_count + 1))

    # Test with curl
    if response=$(curl -s -w "%{http_code}" -o /tmp/health_response "$url" 2>/dev/null); then
        http_code="${response: -3}"
        response_body=$(cat /tmp/health_response)

        if [ "$http_code" = "200" ]; then
            print_status "$name endpoint returned HTTP 200"
            if [ "$VERBOSE" = true ]; then
                echo "Response: $response_body"
            fi

            # Check if response contains expected health status
            if echo "$response_body" | grep -q '"status".*"healthy"'; then
                print_status "$name endpoint reports healthy status"
                pass_count=$((pass_count + 1))
            elif echo "$response_body" | grep -q '"status"'; then
                print_warning "$name endpoint responded but status may not be healthy"
                if [ "$VERBOSE" = true ]; then
                    echo "Response: $response_body"
                fi
            else
                print_warning "$name endpoint responded but format may be unexpected"
                if [ "$VERBOSE" = true ]; then
                    echo "Response: $response_body"
                fi
            fi
        else
            print_error "$name endpoint returned HTTP $http_code"
            if [ "$VERBOSE" = true ]; then
                echo "Response: $response_body"
            fi
        fi
    else
        print_error "Failed to reach $name endpoint"
    fi

    echo
}

# Function to debug monitoring infrastructure
debug_monitoring() {
    if [ "$DEBUG_MONITORING" = true ]; then
        echo
        echo -e "${BLUE}🔍 Debugging Monitoring Infrastructure${NC}"
        echo "====================================="
        echo

        # Check uptime configurations
        echo "📋 Uptime Check Configuration:"
        echo "------------------------------"
        if command -v gcloud >/dev/null 2>&1; then
            gcloud monitoring uptime list-configs --project="$PROJECT_ID" --format="table(displayName,name,httpCheck.path)" 2>/dev/null || print_warning "Could not retrieve uptime check configs"
        else
            print_warning "gcloud CLI not available"
        fi

        echo
        echo "🔍 Recent Uptime Check Results:"
        echo "------------------------------"
        if command -v gcloud >/dev/null 2>&1; then
            echo "Looking for uptime check logs in the last 1 hour:"
            gcloud logging read "resource.type=uptime_url AND timestamp>=now-1h" --project="$PROJECT_ID" --limit=3 --format="value(timestamp,jsonPayload.status)" 2>/dev/null || print_warning "No recent uptime logs found"
        else
            print_warning "gcloud CLI not available for log checking"
        fi

        echo
        echo "📊 Available Uptime Metrics:"
        echo "---------------------------"
        if command -v gcloud >/dev/null 2>&1 && command -v curl >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
            if auth_token=$(gcloud auth print-access-token 2>/dev/null); then
                curl -s -H "Authorization: Bearer $auth_token" \
                  "https://monitoring.googleapis.com/v3/projects/$PROJECT_ID/metricDescriptors?filter=metric.type%3D%22monitoring.googleapis.com%2Fuptime_check%2F*%22" 2>/dev/null | \
                  jq -r '.metricDescriptors[]?.type' 2>/dev/null || print_warning "Could not retrieve uptime metrics"
            else
                print_warning "Could not get authentication token"
            fi
        else
            print_warning "Required tools (gcloud, curl, jq) not available for metrics check"
        fi

        echo
        echo "💡 Monitoring Recommendations:"
        echo "- Dashboard may need 5-15 minutes to show data after uptime check creation"
        echo "- Verify the uptime check is running in GCP Console"
        echo "- Ensure endpoints are accessible from GCP's monitoring infrastructure"
        echo "- Check that log-based metrics are properly configured"
        echo
    fi
}

# Test both endpoints
echo "Testing health endpoints..."
echo

test_endpoint "$PUBLIC_ENDPOINT" "Public"
test_endpoint "$CLOUD_RUN_ENDPOINT" "Cloud Run"

# Run monitoring debug if requested
debug_monitoring

# Cleanup
rm -f /tmp/health_response

# Summary
echo "Health Check Summary"
echo "==================="
echo "Tests run: $test_count"
echo "Tests passed: $pass_count"

if [ "$pass_count" -eq "$test_count" ]; then
    print_status "All health checks passed!"
    exit 0
elif [ "$pass_count" -gt 0 ]; then
    print_warning "Some health checks passed ($pass_count/$test_count)"
    exit 1
else
    print_error "All health checks failed!"
    exit 1
fi
