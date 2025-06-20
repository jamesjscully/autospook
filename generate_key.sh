#!/bin/bash

# AutoSpook Token Generation Script
# Generates secure authentication tokens for API access

set -e

# Configuration
TOKEN_FILE="${TOKEN_FILE:-tokens.txt}"
TOKEN_LENGTH=64
EXPIRY_DAYS=${EXPIRY_DAYS:-30}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_usage() {
    echo "AutoSpook Token Generator"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -g, --generate [NAME]   Generate a new token (with optional name)"
    echo "  -l, --list             List all active tokens"
    echo "  -r, --revoke TOKEN     Revoke a specific token"
    echo "  -c, --cleanup          Remove expired tokens"
    echo "  -v, --validate TOKEN   Validate if token is active"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  TOKEN_FILE             File to store tokens (default: tokens.txt)"
    echo "  EXPIRY_DAYS           Token expiry in days (default: 30)"
    echo ""
    echo "Examples:"
    echo "  $0 --generate admin    # Generate token for 'admin'"
    echo "  $0 --list              # List all tokens"
    echo "  $0 --validate abc123   # Check if token is valid"
}

generate_token() {
    local name=${1:-"user"}
    local token=$(openssl rand -hex $TOKEN_LENGTH)
    local created=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
    local expires=$(date -u -d "+${EXPIRY_DAYS} days" +"%Y-%m-%d %H:%M:%S UTC")
    
    # Ensure token file exists
    touch "$TOKEN_FILE"
    
    # Add token to file
    echo "${token}|${name}|${created}|${expires}|active" >> "$TOKEN_FILE"
    
    echo -e "${GREEN}✅ Token generated successfully!${NC}"
    echo -e "${BLUE}Token:${NC} ${token}"
    echo -e "${BLUE}Name:${NC} ${name}"
    echo -e "${BLUE}Created:${NC} ${created}"
    echo -e "${BLUE}Expires:${NC} ${expires}"
    echo ""
    echo -e "${YELLOW}⚠️  Save this token securely - it cannot be recovered!${NC}"
    
    return 0
}

list_tokens() {
    if [[ ! -f "$TOKEN_FILE" ]]; then
        echo -e "${YELLOW}No tokens found. Generate one with --generate${NC}"
        return 0
    fi
    
    echo -e "${BLUE}Active Tokens:${NC}"
    echo "----------------------------------------"
    
    local count=0
    while IFS='|' read -r token name created expires status; do
        if [[ "$status" == "active" ]]; then
            local current_time=$(date -u +%s)
            local expire_time=$(date -u -d "$expires" +%s 2>/dev/null || echo 0)
            
            if [[ $expire_time -gt $current_time ]]; then
                echo -e "${GREEN}Name:${NC} $name"
                echo -e "${GREEN}Token:${NC} ${token:0:12}...${token: -8}"
                echo -e "${GREEN}Created:${NC} $created"
                echo -e "${GREEN}Expires:${NC} $expires"
                echo "----------------------------------------"
                ((count++))
            fi
        fi
    done < "$TOKEN_FILE"
    
    if [[ $count -eq 0 ]]; then
        echo -e "${YELLOW}No active tokens found${NC}"
    else
        echo -e "${BLUE}Total active tokens: ${count}${NC}"
    fi
}

revoke_token() {
    local token_to_revoke="$1"
    
    if [[ -z "$token_to_revoke" ]]; then
        echo -e "${RED}❌ Error: Token required for revocation${NC}"
        return 1
    fi
    
    if [[ ! -f "$TOKEN_FILE" ]]; then
        echo -e "${RED}❌ Error: No token file found${NC}"
        return 1
    fi
    
    # Create temporary file
    local temp_file=$(mktemp)
    local found=false
    
    while IFS='|' read -r token name created expires status; do
        if [[ "$token" == "$token_to_revoke" ]]; then
            echo "${token}|${name}|${created}|${expires}|revoked" >> "$temp_file"
            found=true
            echo -e "${GREEN}✅ Token revoked: ${name}${NC}"
        else
            echo "${token}|${name}|${created}|${expires}|${status}" >> "$temp_file"
        fi
    done < "$TOKEN_FILE"
    
    if [[ "$found" == true ]]; then
        mv "$temp_file" "$TOKEN_FILE"
    else
        rm "$temp_file"
        echo -e "${RED}❌ Token not found${NC}"
        return 1
    fi
}

validate_token() {
    local token_to_check="$1"
    
    if [[ -z "$token_to_check" ]]; then
        echo -e "${RED}❌ Error: Token required for validation${NC}"
        return 1
    fi
    
    if [[ ! -f "$TOKEN_FILE" ]]; then
        echo -e "${RED}❌ Invalid token${NC}"
        return 1
    fi
    
    local current_time=$(date -u +%s)
    
    while IFS='|' read -r token name created expires status; do
        if [[ "$token" == "$token_to_check" && "$status" == "active" ]]; then
            local expire_time=$(date -u -d "$expires" +%s 2>/dev/null || echo 0)
            
            if [[ $expire_time -gt $current_time ]]; then
                echo -e "${GREEN}✅ Valid token: ${name}${NC}"
                return 0
            else
                echo -e "${RED}❌ Token expired${NC}"
                return 1
            fi
        fi
    done < "$TOKEN_FILE"
    
    echo -e "${RED}❌ Invalid token${NC}"
    return 1
}

cleanup_expired() {
    if [[ ! -f "$TOKEN_FILE" ]]; then
        echo -e "${YELLOW}No tokens to clean up${NC}"
        return 0
    fi
    
    local temp_file=$(mktemp)
    local current_time=$(date -u +%s)
    local cleaned=0
    
    while IFS='|' read -r token name created expires status; do
        local expire_time=$(date -u -d "$expires" +%s 2>/dev/null || echo 0)
        
        if [[ $expire_time -gt $current_time && "$status" == "active" ]]; then
            echo "${token}|${name}|${created}|${expires}|${status}" >> "$temp_file"
        else
            ((cleaned++))
        fi
    done < "$TOKEN_FILE"
    
    mv "$temp_file" "$TOKEN_FILE"
    echo -e "${GREEN}✅ Cleaned up ${cleaned} expired/revoked tokens${NC}"
}

# Main script logic
case "${1:-}" in
    -g|--generate)
        generate_token "$2"
        ;;
    -l|--list)
        list_tokens
        ;;
    -r|--revoke)
        revoke_token "$2"
        ;;
    -c|--cleanup)
        cleanup_expired
        ;;
    -v|--validate)
        validate_token "$2"
        ;;
    -h|--help|"")
        print_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown option: $1${NC}"
        echo ""
        print_usage
        exit 1
        ;;
esac