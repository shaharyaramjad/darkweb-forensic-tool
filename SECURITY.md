# 🔒 Security Guide for Dark Web Forensic Tool

## 🚨 **Critical Security Considerations**

### **Why Security is Essential**

Dark web HTML pages can contain various types of malicious code that could harm your system:

1. **JavaScript Malware** - Executable code that can:
   - Steal browser data and cookies
   - Download additional malware
   - Execute system commands
   - Install keyloggers
   - Run cryptominers
   - Steal cryptocurrency wallets

2. **HTML Injection Attacks** - Malicious scripts embedded in HTML
3. **Drive-by Downloads** - Automatic malware downloads
4. **Cross-Site Scripting (XSS)** - Malicious scripts
5. **Data Exfiltration** - Stealing system information
6. **Encoded Malware** - Base64, URL-encoded, or hex-encoded malicious content

## 🛡️ **Security Features Implemented**

### **1. Security Scanner (`src/utils/security_scanner.py`)**

The tool now includes a comprehensive security scanner that:

#### **Detects Malicious Patterns:**
- JavaScript execution (`<script>`, `eval()`, `exec()`)
- Suspicious URLs (`javascript:`, `data:`, `file://`)
- Event handlers (`onload`, `onclick`, `onerror`)
- Encoded content (Base64, URL-encoded, hex)
- Suspicious attributes and iframes

#### **Sanitization Process:**
- Removes all `<script>` tags
- Removes all `<iframe>`, `<object>`, `<embed>` tags
- Strips event handlers (`on*` attributes)
- Removes encoded malicious content
- Creates safe copies in `data/safe_files/`

### **2. File Size Limits**
- Maximum file size: 10MB
- Prevents processing of suspiciously large files

### **3. Safe Processing Workflow**
```
Original File → Security Scan → Threat Detection → Sanitization → Safe Processing
```

## 🔧 **How to Use Security Features**

### **Command Line Interface**
```bash
# Security scanning is enabled by default
python src/main.py

# To disable security scanning (NOT RECOMMENDED)
# Edit src/main.py and set: ENABLE_SECURITY_SCAN = False
```

### **Web Interface**
1. Upload HTML files
2. Security scanning is enabled by default
3. View security reports in expandable sections
4. Download sanitized versions automatically

### **Test Security Scanner**
```bash
python test_security_scanner.py
```

## 📋 **Security Best Practices**

### **1. Always Enable Security Scanning**
```python
ENABLE_SECURITY_SCAN = True  # ✅ RECOMMENDED
ENABLE_SECURITY_SCAN = False # ❌ DANGEROUS
```

### **2. Use Isolated Environment**
- Run in a virtual machine
- Use containerized environment
- Isolate from production systems

### **3. Monitor File Sources**
- Only process files from trusted sources
- Verify file integrity with hashes
- Keep original files separate from processed files

### **4. Regular Security Updates**
- Update dependencies regularly
- Monitor for new threat patterns
- Keep security scanner updated

## 🚨 **Threat Detection Examples**

### **JavaScript Malware**
```html
<script>
    alert('This is malicious!');
    eval('alert("More malicious code")');
    document.location = 'javascript:alert("XSS")';
</script>
```

### **Encoded Malware**
```html
<!-- Base64 encoded -->
<script>eval(atob('YWxlcnQoIk1hbGljaW91cyBjb250ZW50ISIp'))</script>

<!-- URL encoded -->
<p>%3Cscript%3Ealert('XSS')%3C/script%3E</p>

<!-- Hex encoded -->
<p>\x3Cscript\x3Ealert('XSS')\x3C/script\x3E</p>
```

### **Event Handler Attacks**
```html
<img src="x" onerror="alert('XSS via onerror')">
<a href="javascript:alert('XSS via href')">Click me</a>
```

## 📊 **Security Reports**

The tool generates detailed security reports showing:

- **Threat Detection**: Number and types of threats found
- **File Statistics**: Original vs sanitized file sizes
- **Sanitization Results**: What was removed/cleaned
- **Safety Status**: Whether file is safe to process

### **Example Security Report:**
```
🔒 SECURITY SCAN REPORT
File: malicious_test.html
Safe: ❌ NO

Threats Detected: 3

🚨 THREATS FOUND:
1. javascript_execution: 3 matches found
2. suspicious_attributes: 2 matches found
3. Encoded content detected: 1 instances

📊 STATISTICS:
Original size: 1250 characters
Sanitized size: 450 characters
Size reduction: 800 characters
```

## 🔍 **Manual Security Checks**

### **Before Processing Files:**
1. **Check file size** - Suspiciously large files may contain malware
2. **Verify source** - Only process files from trusted sources
3. **Check file type** - Ensure files are actually HTML
4. **Scan with antivirus** - Use additional security tools

### **After Processing:**
1. **Review security reports** - Check what threats were detected
2. **Verify sanitized files** - Ensure malicious content was removed
3. **Monitor system** - Watch for unusual activity
4. **Clean up** - Remove original files if no longer needed

## ⚠️ **Disclaimers**

### **No Guarantee of Complete Safety**
- The security scanner provides protection but cannot guarantee 100% safety
- New malware variants may not be detected immediately
- Always use additional security measures

### **Use at Your Own Risk**
- Processing dark web content inherently carries risks
- The tool is designed for forensic analysis, not general web browsing
- Always use in isolated environments

## 🆘 **Emergency Procedures**

### **If Malware is Detected:**
1. **Stop processing immediately**
2. **Isolate the system** - Disconnect from network
3. **Scan with antivirus** - Use multiple tools
4. **Check system integrity** - Monitor for unusual activity
5. **Report incidents** - Document what happened

### **If System is Compromised:**
1. **Disconnect from network**
2. **Take system snapshot** - For forensic analysis
3. **Contact IT security** - If in organizational environment
4. **Consider system reimage** - If necessary

## 📞 **Support and Updates**

### **Security Updates:**
- Monitor GitHub for security updates
- Update dependencies regularly
- Report new threat patterns

### **Getting Help:**
- Check security reports for details
- Review logs for error messages
- Test with known safe files first

---

**⚠️ IMPORTANT: Always enable security scanning when processing dark web content!** 