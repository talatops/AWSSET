import jsPDF from 'jspdf';
import 'jspdf-autotable';

class DataExportService {
  constructor() {
    this.pdf = null;
  }

  async exportUserData(user, userData = {}) {
    try {
      this.pdf = new jsPDF();
      
      // Add header
      this.addHeader();
      
      // Add user profile section
      this.addUserProfile(user);
      
      // Add AWS resources section (if available)
      if (userData.awsResources) {
        this.addAWSResources(userData.awsResources);
      }
      
      // Add chat history section (if available)
      if (userData.chatHistory) {
        this.addChatHistory(userData.chatHistory);
      }
      
      // Add settings section
      this.addSettings(userData.settings);
      
      // Add footer
      this.addFooter();
      
      // Generate filename
      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `awsset-export-${user.username}-${timestamp}.pdf`;
      
      // Save PDF
      this.pdf.save(filename);
      
      return { success: true, filename };
    } catch (error) {
      console.error('Error exporting data:', error);
      return { success: false, error: error.message };
    }
  }

  addHeader() {
    // Add logo placeholder
    this.pdf.setFillColor(0, 212, 255); // Cyan color
    this.pdf.rect(20, 20, 30, 15, 'F');
    
    // Add title
    this.pdf.setFontSize(24);
    this.pdf.setTextColor(15, 20, 25); // Dark color
    this.pdf.text('AWSSET', 60, 30);
    
    // Add subtitle
    this.pdf.setFontSize(14);
    this.pdf.setTextColor(100, 100, 100);
    this.pdf.text('Data Export Report', 60, 40);
    
    // Add export info
    this.pdf.setFontSize(10);
    this.pdf.setTextColor(150, 150, 150);
    this.pdf.text(`Generated on: ${new Date().toLocaleString()}`, 60, 50);
    
    this.pdf.setFontSize(10);
    this.pdf.setTextColor(150, 150, 150);
    this.pdf.text(`Version: 2.1.0`, 60, 60);
  }

  addUserProfile(user) {
    this.pdf.addPage();
    
    // Section title
    this.pdf.setFontSize(16);
    this.pdf.setTextColor(15, 20, 25);
    this.pdf.text('User Profile', 20, 20);
    
    // User information table
    const userData = [
      ['Username', user.username || 'N/A'],
      ['Email', user.email || 'N/A'],
      ['Full Name', user.full_name || 'N/A'],
      ['Provider', user.provider || 'Local'],
      ['AWS Region', user.aws_region || 'Not Set'],
      ['Profile Customized', user.profile_customized ? 'Yes' : 'No'],
      ['Account Created', user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'],
      ['Last Login', user.last_login ? new Date(user.last_login).toLocaleDateString() : 'N/A']
    ];
    
    this.pdf.autoTable({
      startY: 30,
      head: [['Field', 'Value']],
      body: userData,
      theme: 'grid',
      headStyles: { fillColor: [0, 212, 255] },
      styles: { fontSize: 10 }
    });
  }

  addAWSResources(awsResources) {
    if (!awsResources || Object.keys(awsResources).length === 0) {
      return;
    }
    
    this.pdf.addPage();
    
    // Section title
    this.pdf.setFontSize(16);
    this.pdf.setTextColor(15, 20, 25);
    this.pdf.text('AWS Resources Summary', 20, 20);
    
    let yPosition = 40;
    
    // EC2 Instances
    if (awsResources.ec2) {
      this.pdf.setFontSize(14);
      this.pdf.setTextColor(0, 100, 200);
      this.pdf.text('EC2 Instances', 20, yPosition);
      
      const ec2Data = awsResources.ec2.instances?.map(instance => [
        instance.id || 'N/A',
        instance.name || 'N/A',
        instance.state || 'N/A',
        instance.type || 'N/A',
        instance.region || 'N/A'
      ]) || [];
      
      if (ec2Data.length > 0) {
        this.pdf.autoTable({
          startY: yPosition + 10,
          head: [['Instance ID', 'Name', 'State', 'Type', 'Region']],
          body: ec2Data,
          theme: 'grid',
          headStyles: { fillColor: [0, 212, 255] },
          styles: { fontSize: 9 }
        });
        yPosition = this.pdf.lastAutoTable.finalY + 20;
      }
    }
    
    // S3 Buckets
    if (awsResources.s3) {
      this.pdf.setFontSize(14);
      this.pdf.setTextColor(0, 100, 200);
      this.pdf.text('S3 Buckets', 20, yPosition);
      
      const s3Data = awsResources.s3.buckets?.map(bucket => [
        bucket.name || 'N/A',
        bucket.region || 'N/A',
        bucket.creationDate ? new Date(bucket.creationDate).toLocaleDateString() : 'N/A'
      ]) || [];
      
      if (s3Data.length > 0) {
        this.pdf.autoTable({
          startY: yPosition + 10,
          head: [['Bucket Name', 'Region', 'Creation Date']],
          body: s3Data,
          theme: 'grid',
          headStyles: { fillColor: [0, 212, 255] },
          styles: { fontSize: 9 }
        });
        yPosition = this.pdf.lastAutoTable.finalY + 20;
      }
    }
    
    // Lambda Functions
    if (awsResources.lambda) {
      this.pdf.setFontSize(14);
      this.pdf.setTextColor(0, 100, 200);
      this.pdf.text('Lambda Functions', 20, yPosition);
      
      const lambdaData = awsResources.lambda.functions?.map(func => [
        func.name || 'N/A',
        func.runtime || 'N/A',
        func.handler || 'N/A',
        func.lastModified ? new Date(func.lastModified).toLocaleDateString() : 'N/A'
      ]) || [];
      
      if (lambdaData.length > 0) {
        this.pdf.autoTable({
          startY: yPosition + 10,
          head: [['Function Name', 'Runtime', 'Handler', 'Last Modified']],
          body: lambdaData,
          theme: 'grid',
          headStyles: { fillColor: [0, 212, 255] },
          styles: { fontSize: 9 }
        });
      }
    }
  }

  addChatHistory(chatHistory) {
    if (!chatHistory || chatHistory.length === 0) {
      return;
    }
    
    this.pdf.addPage();
    
    // Section title
    this.pdf.setFontSize(16);
    this.pdf.setTextColor(15, 20, 25);
    this.pdf.text('Chat History (Last 50 Messages)', 20, 20);
    
    // Chat messages table
    const chatData = chatHistory.slice(0, 50).map(message => [
      message.timestamp ? new Date(message.timestamp).toLocaleString() : 'N/A',
      message.role || 'N/A',
      message.content ? this.truncateText(message.content, 80) : 'N/A'
    ]);
    
    this.pdf.autoTable({
      startY: 30,
      head: [['Timestamp', 'Role', 'Message']],
      body: chatData,
      theme: 'grid',
      headStyles: { fillColor: [0, 212, 255] },
      styles: { fontSize: 8 },
      columnStyles: {
        0: { cellWidth: 30 },
        1: { cellWidth: 20 },
        2: { cellWidth: 140 }
      }
    });
  }

  addSettings(settings) {
    this.pdf.addPage();
    
    // Section title
    this.pdf.setFontSize(16);
    this.pdf.setTextColor(15, 20, 25);
    this.pdf.text('User Settings & Preferences', 20, 20);
    
    if (settings) {
      const settingsData = Object.entries(settings).map(([key, value]) => [
        this.formatSettingKey(key),
        typeof value === 'boolean' ? (value ? 'Enabled' : 'Disabled') : String(value)
      ]);
      
      this.pdf.autoTable({
        startY: 30,
        head: [['Setting', 'Value']],
        body: settingsData,
        theme: 'grid',
        headStyles: { fillColor: [0, 212, 255] },
        styles: { fontSize: 10 }
      });
    } else {
      this.pdf.setFontSize(12);
      this.pdf.setTextColor(100, 100, 100);
      this.pdf.text('No custom settings found', 20, 40);
    }
  }

  addFooter() {
    const pageCount = this.pdf.internal.getNumberOfPages();
    
    for (let i = 1; i <= pageCount; i++) {
      this.pdf.setPage(i);
      
      // Footer line
      this.pdf.setDrawColor(200, 200, 200);
      this.pdf.line(20, 280, 190, 280);
      
      // Footer text
      this.pdf.setFontSize(8);
      this.pdf.setTextColor(150, 150, 150);
      this.pdf.text(`Page ${i} of ${pageCount}`, 20, 290);
      this.pdf.text('AWSSET - AI-Powered Cloud Management', 190, 290, { align: 'right' });
    }
  }

  formatSettingKey(key) {
    return key
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, str => str.toUpperCase())
      .replace(/_/g, ' ');
  }

  truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  }

  // Export specific data types
  async exportProfileOnly(user) {
    return this.exportUserData(user, {});
  }

  async exportFullData(user, userData) {
    return this.exportUserData(user, userData);
  }

  // Export as JSON (alternative format)
  exportAsJSON(user, userData) {
    try {
      const exportData = {
        exportInfo: {
          timestamp: new Date().toISOString(),
          version: '2.1.0',
          format: 'JSON'
        },
        user: {
          username: user.username,
          email: user.email,
          full_name: user.full_name,
          provider: user.provider,
          aws_region: user.aws_region,
          profile_customized: user.profile_customized,
          created_at: user.created_at,
          last_login: user.last_login
        },
        awsResources: userData.awsResources || {},
        settings: userData.settings || {},
        chatHistory: userData.chatHistory ? userData.chatHistory.slice(0, 100) : []
      };

      const dataStr = JSON.stringify(exportData, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      
      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `awsset-export-${user.username}-${timestamp}.json`;
      
      const link = document.createElement('a');
      link.href = URL.createObjectURL(dataBlob);
      link.download = filename;
      link.click();
      
      return { success: true, filename };
    } catch (error) {
      console.error('Error exporting JSON:', error);
      return { success: false, error: error.message };
    }
  }
}

export default new DataExportService();
