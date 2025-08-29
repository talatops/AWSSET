#!/bin/bash

# AWS Chatbot - SSL Certificate Setup Script
# Generates self-signed certificates for development or sets up production certificates

set -e

# Configuration
SSL_DIR="nginx/ssl"
CERT_FILE="$SSL_DIR/cert.pem"
KEY_FILE="$SSL_DIR/key.pem"
DOMAIN="localhost"
COUNTRY="US"
STATE="Development"
CITY="Local"
ORGANIZATION="AWS Chatbot"
DAYS=365

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[SSL Setup]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if running as root (for production setup)
check_root() {
    if [[ $EUID -eq 0 ]]; then
        warn "Running as root. This is only recommended for production setup."
    fi
}

# Create SSL directory
create_ssl_directory() {
    log "Creating SSL directory..."
    mkdir -p "$SSL_DIR"
    chmod 755 "$SSL_DIR"
}

# Generate self-signed certificate for development
generate_self_signed() {
    log "Generating self-signed certificate for development..."
    
    # Check if OpenSSL is installed
    if ! command -v openssl &> /dev/null; then
        error "OpenSSL is not installed. Please install OpenSSL first."
        exit 1
    fi
    
    # Generate private key
    info "Generating private key..."
    openssl genrsa -out "$KEY_FILE" 2048
    
    # Generate certificate signing request
    info "Generating certificate signing request..."
    openssl req -new -key "$KEY_FILE" -out "$SSL_DIR/cert.csr" -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORGANIZATION/CN=$DOMAIN"
    
    # Generate self-signed certificate
    info "Generating self-signed certificate..."
    openssl x509 -req -in "$SSL_DIR/cert.csr" -signkey "$KEY_FILE" -out "$CERT_FILE" -days "$DAYS" -extensions v3_req -extfile <(
        echo '[v3_req]'
        echo 'basicConstraints = CA:FALSE'
        echo 'keyUsage = nonRepudiation, digitalSignature, keyEncipherment'
        echo 'subjectAltName = @alt_names'
        echo '[alt_names]'
        echo 'DNS.1 = localhost'
        echo 'DNS.2 = *.localhost'
        echo 'IP.1 = 127.0.0.1'
        echo 'IP.2 = ::1'
    )
    
    # Clean up CSR
    rm "$SSL_DIR/cert.csr"
    
    # Set appropriate permissions
    chmod 644 "$CERT_FILE"
    chmod 600 "$KEY_FILE"
    
    log "Self-signed certificate generated successfully!"
    info "Certificate: $CERT_FILE"
    info "Private Key: $KEY_FILE"
    info "Valid for: $DAYS days"
}

# Setup Let's Encrypt certificate (for production)
setup_letsencrypt() {
    local domain="$1"
    local email="$2"
    
    log "Setting up Let's Encrypt certificate for $domain..."
    
    # Check if certbot is installed
    if ! command -v certbot &> /dev/null; then
        error "Certbot is not installed. Installing..."
        
        # Install certbot based on OS
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y certbot python3-certbot-nginx
            elif command -v yum &> /dev/null; then
                sudo yum install -y certbot python3-certbot-nginx
            else
                error "Unsupported Linux distribution. Please install certbot manually."
                exit 1
            fi
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            if command -v brew &> /dev/null; then
                brew install certbot
            else
                error "Homebrew not found. Please install certbot manually."
                exit 1
            fi
        else
            error "Unsupported operating system. Please install certbot manually."
            exit 1
        fi
    fi
    
    # Generate certificate
    info "Requesting certificate from Let's Encrypt..."
    sudo certbot certonly --standalone \
        --preferred-challenges http \
        --email "$email" \
        --agree-tos \
        --no-eff-email \
        -d "$domain"
    
    # Copy certificates to nginx directory
    info "Copying certificates to nginx directory..."
    sudo cp "/etc/letsencrypt/live/$domain/fullchain.pem" "$CERT_FILE"
    sudo cp "/etc/letsencrypt/live/$domain/privkey.pem" "$KEY_FILE"
    
    # Set permissions
    sudo chown $USER:$USER "$CERT_FILE" "$KEY_FILE"
    chmod 644 "$CERT_FILE"
    chmod 600 "$KEY_FILE"
    
    log "Let's Encrypt certificate setup complete!"
    
    # Setup auto-renewal
    setup_auto_renewal "$domain"
}

# Setup automatic certificate renewal
setup_auto_renewal() {
    local domain="$1"
    
    log "Setting up automatic certificate renewal..."
    
    # Create renewal script
    cat > "$SSL_DIR/renew-cert.sh" << EOF
#!/bin/bash
# Auto-renewal script for Let's Encrypt certificates

certbot renew --quiet --no-self-upgrade

# Copy renewed certificates
if [ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
    cp "/etc/letsencrypt/live/$domain/fullchain.pem" "$CERT_FILE"
    cp "/etc/letsencrypt/live/$domain/privkey.pem" "$KEY_FILE"
    
    # Reload nginx
    docker-compose exec nginx nginx -s reload
fi
EOF
    
    chmod +x "$SSL_DIR/renew-cert.sh"
    
    # Add to crontab (run twice daily)
    (crontab -l 2>/dev/null; echo "0 */12 * * * $(pwd)/$SSL_DIR/renew-cert.sh") | crontab -
    
    info "Auto-renewal setup complete. Certificates will be checked twice daily."
}

# Validate certificate
validate_certificate() {
    log "Validating certificate..."
    
    if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
        error "Certificate or key file not found!"
        return 1
    fi
    
    # Check certificate validity
    if openssl x509 -in "$CERT_FILE" -text -noout > /dev/null 2>&1; then
        info "Certificate is valid"
        
        # Show certificate details
        info "Certificate details:"
        openssl x509 -in "$CERT_FILE" -text -noout | grep -E "(Subject:|Issuer:|Not Before:|Not After:|DNS:|IP Address:)"
        
        return 0
    else
        error "Certificate is invalid!"
        return 1
    fi
}

# Main function
main() {
    info "AWS Chatbot SSL Certificate Setup"
    echo "=================================="
    
    check_root
    create_ssl_directory
    
    # Parse command line arguments
    case "${1:-self-signed}" in
        "self-signed"|"dev"|"development")
            generate_self_signed
            ;;
        "letsencrypt"|"prod"|"production")
            if [ -z "$2" ] || [ -z "$3" ]; then
                error "Usage: $0 letsencrypt <domain> <email>"
                error "Example: $0 letsencrypt example.com admin@example.com"
                exit 1
            fi
            setup_letsencrypt "$2" "$3"
            ;;
        "validate"|"check")
            validate_certificate
            exit $?
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [option] [arguments]"
            echo ""
            echo "Options:"
            echo "  self-signed, dev     Generate self-signed certificate for development (default)"
            echo "  letsencrypt, prod    Setup Let's Encrypt certificate for production"
            echo "                       Usage: $0 letsencrypt <domain> <email>"
            echo "  validate, check      Validate existing certificate"
            echo "  help                 Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Generate self-signed certificate"
            echo "  $0 self-signed                       # Generate self-signed certificate"
            echo "  $0 letsencrypt example.com admin@example.com  # Setup Let's Encrypt"
            echo "  $0 validate                          # Validate existing certificate"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            error "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
    
    # Validate the generated/setup certificate
    if validate_certificate; then
        log "SSL setup completed successfully!"
        echo ""
        info "Next steps:"
        echo "1. Update .docker.env with TLS_ENABLED=true"
        echo "2. Run: docker-compose up --build"
        echo "3. Access your application at: https://localhost"
        echo ""
        if [ "${1:-self-signed}" = "self-signed" ] || [ "$1" = "dev" ] || [ "$1" = "development" ]; then
            warn "For development certificates, your browser will show a security warning."
            warn "This is normal for self-signed certificates. Click 'Advanced' and 'Proceed to localhost'."
        fi
    else
        error "SSL setup failed!"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
