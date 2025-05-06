import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Medical Record component to fetch and display a patient's medical record 
// with the additional OTP security layer
const MedicalRecordViewer = () => {
  const [medicalRecord, setMedicalRecord] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [otpRequested, setOtpRequested] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [medAccessToken, setMedAccessToken] = useState(null);
  const [otpVerificationStep, setOtpVerificationStep] = useState(false);
  
  // Get token from authentication state/context
  const getAuthToken = () => {
    // In a real app, this would come from your auth context or state management
    return localStorage.getItem('auth_token');
  };
  
  // Request a medical record-specific OTP
  const requestMedicalRecordOTP = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL}/patient/medical-record/request-otp/`,
        {},
        {
          headers: {
            Authorization: `Bearer ${getAuthToken()}`
          }
        }
      );
      
      setOtpRequested(true);
      setOtpVerificationStep(true);
      setLoading(false);
    } catch (err) {
      setError('Failed to request medical record access code. Please try again.');
      setLoading(false);
      console.error('Error requesting medical record OTP:', err);
    }
  };
  
  // Verify the medical record OTP
  const verifyMedicalRecordOTP = async (e) => {
    e.preventDefault();
    
    if (!otpCode.trim() || otpCode.length < 6) {
      setError('Please enter a valid access code');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL}/patient/medical-record/verify-otp/`,
        { otp: otpCode },
        {
          headers: {
            Authorization: `Bearer ${getAuthToken()}`
          }
        }
      );
      
      // Store the medical record access token
      const token = response.data.med_access_token;
      setMedAccessToken(token);
      
      // Set expiry time in localStorage with the token
      const expiresAt = new Date().getTime() + (response.data.expires_in * 1000);
      localStorage.setItem('med_access_token', token);
      localStorage.setItem('med_access_expires_at', expiresAt.toString());
      
      // Now fetch the medical record
      fetchMedicalRecord(token);
      
      setOtpVerificationStep(false);
      setLoading(false);
    } catch (err) {
      setError('Invalid or expired access code. Please try again.');
      setLoading(false);
      console.error('Error verifying medical record OTP:', err);
    }
  };
  
  // Check if we have a valid med access token
  const checkMedAccessToken = () => {
    const token = localStorage.getItem('med_access_token');
    const expiresAt = localStorage.getItem('med_access_expires_at');
    
    if (token && expiresAt) {
      const now = new Date().getTime();
      if (now < parseInt(expiresAt)) {
        setMedAccessToken(token);
        return token;
      } else {
        // Clear expired token
        localStorage.removeItem('med_access_token');
        localStorage.removeItem('med_access_expires_at');
      }
    }
    
    return null;
  };
  
  // Fetch medical record data
  const fetchMedicalRecord = async (medToken = null) => {
    setLoading(true);
    setError(null);
    
    const token = medToken || medAccessToken;
    if (!token) {
      setError('Medical record access token required');
      setLoading(false);
      return;
    }
    
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL}/patient/medical-record/`,
        {
          headers: {
            Authorization: `Bearer ${getAuthToken()}`,
            'X-Med-Access-Token': token
          }
        }
      );
      
      setMedicalRecord(response.data);
      setLoading(false);
    } catch (err) {
      setLoading(false);
      
      // Handle different error cases
      if (err.response) {
        if (err.response.data && err.response.data.code === 'MED_ACCESS_EXPIRED') {
          // The medical record access has expired
          setError('Your access to medical records has expired. Please verify again.');
          localStorage.removeItem('med_access_token');
          localStorage.removeItem('med_access_expires_at');
          setMedAccessToken(null);
        } else if (err.response.data && err.response.data.code === 'MED_ACCESS_REQUIRED') {
          // Need to request medical record access
          setError('Medical record access required');
          setMedAccessToken(null);
        } else {
          setError('Failed to load medical record data. Please try again later.');
        }
      } else {
        setError('Network error. Please check your connection and try again.');
      }
      
      console.error('Error fetching medical record:', err);
    }
  };
  
  useEffect(() => {
    // Check if we have a valid med access token on component mount
    const token = checkMedAccessToken();
    
    if (token) {
      // If we have a valid token, fetch the medical record
      fetchMedicalRecord(token);
    }
  }, []);
  
  // Handle OTP input changes
  const handleOtpChange = (e) => {
    setOtpCode(e.target.value);
  };
  
  if (loading) {
    return <div className="loading">Loading medical records...</div>;
  }
  
  if (otpVerificationStep) {
    return (
      <div className="medical-record-otp">
        <h2>Medical Record Access Verification</h2>
        <p>
          For your security, we've sent a verification code to your email.
          Please enter the code below to access your medical records.
        </p>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={verifyMedicalRecordOTP}>
          <div className="form-group">
            <label htmlFor="otpCode">Verification Code</label>
            <input
              type="text"
              id="otpCode"
              value={otpCode}
              onChange={handleOtpChange}
              placeholder="Enter 6-digit code"
              maxLength="6"
              required
            />
          </div>
          
          <button type="submit" className="verify-button" disabled={loading}>
            {loading ? 'Verifying...' : 'Verify & Access Records'}
          </button>
        </form>
        
        <p className="help-text">
          Didn't receive a code? <button onClick={requestMedicalRecordOTP} disabled={loading}>
            Resend Code
          </button>
        </p>
      </div>
    );
  }
  
  if (!medAccessToken) {
    return (
      <div className="medical-record-request">
        <h2>Access Your Medical Records</h2>
        <p>
          Your medical records contain sensitive information. 
          For your security, we require additional verification before displaying this data.
        </p>
        
        {error && <div className="error-message">{error}</div>}
        
        <button onClick={requestMedicalRecordOTP} disabled={loading} className="request-button">
          {loading ? 'Requesting...' : 'Request Access Code'}
        </button>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="error-container">
        <p className="error-message">{error}</p>
        <button onClick={requestMedicalRecordOTP} className="retry-button">
          Request New Access Code
        </button>
      </div>
    );
  }
  
  return (
    <div className="medical-record-container">
      <div className="header">
        <h2>Your Medical Records</h2>
        <span className="secure-badge">Secured Access</span>
      </div>
      
      {medicalRecord ? (
        <div className="medical-record-data">
          <div className="record-section">
            <h3>Patient Information</h3>
            <div className="record-field">
              <label>Hospital Patient Number (HPN):</label>
              <span>{medicalRecord.hpn || 'Not Available'}</span>
            </div>
            <div className="record-field">
              <label>Blood Type:</label>
              <span>{medicalRecord.blood_type || 'Not Available'}</span>
            </div>
          </div>
          
          <div className="record-section">
            <h3>Medical Information</h3>
            <div className="record-field">
              <label>Allergies:</label>
              <span>{medicalRecord.allergies || 'None reported'}</span>
            </div>
            <div className="record-field">
              <label>Chronic Conditions:</label>
              <span>{medicalRecord.chronic_conditions || 'None reported'}</span>
            </div>
            <div className="record-field">
              <label>Last Visit Date:</label>
              <span>{medicalRecord.last_visit_date || 'No recent visits'}</span>
            </div>
          </div>
          
          <div className="record-section">
            <h3>Emergency Contact</h3>
            <div className="record-field">
              <label>Name:</label>
              <span>{medicalRecord.emergency_contact_name || 'Not provided'}</span>
            </div>
            <div className="record-field">
              <label>Phone:</label>
              <span>{medicalRecord.emergency_contact_phone || 'Not provided'}</span>
            </div>
          </div>
          
          <div className="record-section">
            <h3>Diagnoses</h3>
            {medicalRecord.diagnoses && medicalRecord.diagnoses.length > 0 ? (
              <ul className="diagnoses-list">
                {medicalRecord.diagnoses.map((diagnosis, index) => (
                  <li key={index}>{diagnosis}</li>
                ))}
              </ul>
            ) : (
              <p>No diagnoses recorded</p>
            )}
          </div>
          
          <div className="record-section">
            <h3>Treatments</h3>
            {medicalRecord.treatments && medicalRecord.treatments.length > 0 ? (
              <ul className="treatments-list">
                {medicalRecord.treatments.map((treatment, index) => (
                  <li key={index}>{treatment}</li>
                ))}
              </ul>
            ) : (
              <p>No treatments recorded</p>
            )}
          </div>
        </div>
      ) : (
        <div className="no-records">
          <p>No medical records available.</p>
        </div>
      )}
      
      <div className="security-note">
        <p>
          <strong>Security Note:</strong> Your medical record access will expire after 30 minutes.
          If you need to access your records again later, you'll need to verify your identity again.
        </p>
      </div>
    </div>
  );
};

export default MedicalRecordViewer; 