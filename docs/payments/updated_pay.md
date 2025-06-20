Medical Appointment Payment System Documentation

  Overview

  The Medical Appointment Payment System supports both payment-disabled (free appointments) and payment-enabled modes with seamless switching. The system
  implements a payment-first approach where users can pay before appointment creation, ensuring better user experience and reduced abandoned bookings.

  Architecture Overview

  Frontend (React/TypeScript) → Backend (Django) → Payment Provider (Paystack)
       ↓                           ↓                        ↓
  PaymentService.ts          PaymentInitializeView      Paystack API
  BookAppointment.tsx        Appointment Model          Payment Processing
  PaymentModal.tsx           Notification System        Transaction Verification

  ---
  Backend Implementation

  1. Payment Configuration

  Environment Variables (.env)

  # Payment System Configuration
  PAYMENTS_ENABLED=False  # Set to True to enable payments
  PAYSTACK_SECRET_KEY=sk_test_your_secret_key_here
  PAYSTACK_PUBLIC_KEY=pk_test_your_public_key_here

  # Payment Provider Settings
  DEFAULT_PAYMENT_PROVIDER=paystack
  PAYMENT_CURRENCY=NGN
  PAYMENT_TIMEOUT_SECONDS=900  # 15 minutes

  Django Settings (server/settings.py)

  # Payment Configuration
  PAYMENTS_ENABLED = os.getenv('PAYMENTS_ENABLED', 'False').lower() == 'true'
  PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
  PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY')

  # Payment Providers
  PAYMENT_PROVIDERS = {
      'paystack': {
          'secret_key': PAYSTACK_SECRET_KEY,
          'public_key': PAYSTACK_PUBLIC_KEY,
          'base_url': 'https://api.paystack.co',
      }
  }

  DEFAULT_PAYMENT_PROVIDER = 'paystack'
  PAYMENT_CURRENCY = 'NGN'

  2. Core Models

  Appointment Model (api/models/medical/appointment.py)

  class Appointment(models.Model):
      # Core fields
      appointment_id = models.CharField(max_length=20, unique=True)
      patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
      doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, null=True, blank=True)
      hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
      department = models.ForeignKey(Department, on_delete=models.CASCADE)

      # Appointment details
      appointment_date = models.DateTimeField()
      appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPE_CHOICES)
      priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
      status = models.CharField(max_length=20, choices=STATUS_CHOICES)

      # Medical information
      chief_complaint = models.TextField()
      symptoms = models.TextField(blank=True)
      symptoms_data = models.JSONField(default=list)  # Structured symptoms data
      medical_history = models.TextField(blank=True)
      allergies = models.TextField(blank=True)
      current_medications = models.TextField(blank=True)

      # Payment fields
      payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES)
      payment_required = models.BooleanField(default=True)

      def save(self, *args, **kwargs):
          # Generate appointment ID if new
          if not self.appointment_id:
              self.appointment_id = self.generate_appointment_id()

          # Track status changes for notifications
          is_new_appointment = self.pk is None
          old_status = None
          if not is_new_appointment:
              old_instance = Appointment.objects.get(pk=self.pk)
              old_status = old_instance.status

          super().save(*args, **kwargs)

          # Send notifications after save
          self._send_appointment_notifications(is_new_appointment, old_status)

  Payment Transaction Model (api/models/medical/payment_transaction.py)

  class PaymentTransaction(models.Model):
      # Core fields
      payment_id = models.CharField(max_length=100, unique=True)
      appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, null=True, blank=True)
      patient = models.ForeignKey(User, on_delete=models.CASCADE)

      # Payment details
      amount = models.DecimalField(max_digits=10, decimal_places=2)
      currency = models.CharField(max_length=3, default='NGN')
      payment_method = models.CharField(max_length=50)
      payment_provider = models.CharField(max_length=50)

      # Status tracking
      status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES)
      provider_reference = models.CharField(max_length=200, unique=True)

      # Encrypted data storage
      encrypted_booking_data = models.TextField(blank=True)

      def _get_signer(self):
          """Get a fresh signer instance for thread safety"""
          from django.core.signing import Signer
          return Signer(salt='payment_transaction')

      def encrypt_booking_data(self, data):
          """Encrypt booking data for secure storage"""
          try:
              signer = self._get_signer()
              return signer.sign(json.dumps(data))
          except Exception as e:
              logger.error(f"Encryption failed: {e}")
              return json.dumps(data)  # Fallback to unencrypted

  3. Payment Views

  Payment Initialize View (api/views/payment/payment_views.py)

  class PaymentInitializeView(APIView):
      """Initialize a payment for an appointment"""
      permission_classes = [IsAuthenticated]

      def post(self, request):
          try:
              # Debug logging
              logger.debug(f"Payment initialize request data: {request.data}")

              # Ensure symptoms_data is available
              if 'symptoms_data' not in request.data:
                  request.data['symptoms_data'] = []

              # Check if payments are disabled
              if not getattr(settings, 'PAYMENTS_ENABLED', True):
                  logger.info("Payment disabled - handling appointment creation with waived payment")
                  return self._handle_disabled_payment_flow(request)

              # Normal payment flow
              return self._handle_enabled_payment_flow(request)

          except Exception as e:
              logger.error(f"Payment initialization error: {str(e)}")
              return Response({
                  'error': f'Payment initialization failed: {str(e)}'
              }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

      def _handle_disabled_payment_flow(self, request):
          """Handle appointment creation when payments are disabled"""
          appointment_id = request.data.get('appointment_id')

          if appointment_id:
              # Traditional flow: update existing appointment
              appointment = get_object_or_404(Appointment, id=appointment_id)
              appointment.payment_status = 'waived'
              appointment.payment_required = False
              appointment.save()

              return Response({
                  'success': True,
                  'payments_enabled': False,
                  'message': 'Appointment payment waived successfully',
                  'appointment_id': appointment.appointment_id
              })
          else:
              # Payment-first flow: create appointment directly
              return self._create_appointment_with_waived_payment(request)

      def _create_appointment_with_waived_payment(self, request):
          """Create appointment directly when payments are disabled"""
          # Extract and validate booking details
          booking_details = {
              'department_id': request.data.get('department_id'),
              'appointment_date': request.data.get('appointment_date'),
              'symptoms_data': request.data.get('symptoms_data', []),
              # ... other fields
          }

          # Ensure symptoms_data is a proper list
          symptoms_data = booking_details.get('symptoms_data', [])
          if not isinstance(symptoms_data, list):
              symptoms_data = []

          # Create appointment with waived payment
          appointment = Appointment.objects.create(
              appointment_id=Appointment.generate_appointment_id(),
              patient=request.user,
              symptoms_data=symptoms_data,
              payment_status='waived',
              payment_required=False,
              # ... other fields
          )

          return Response({
              'success': True,
              'payments_enabled': False,
              'message': 'Appointment created successfully with waived payment',
              'appointment_id': appointment.appointment_id
          })

  Payment Status View

  class PaymentStatusView(APIView):
      """Check if payment system is enabled"""
      permission_classes = [IsAuthenticated]

      def get(self, request):
          return Response({
              'payments_enabled': getattr(settings, 'PAYMENTS_ENABLED', True),
              'message': 'Payment system status',
              'available_providers': list(settings.PAYMENT_PROVIDERS.keys()),
              'free_appointments': not getattr(settings, 'PAYMENTS_ENABLED', True)
          })

  4. URL Configuration (api/urls.py)

  # Payment URLs
  path('api/payments/status/', PaymentStatusView.as_view(), name='payment-status'),
  path('api/payments/initialize/', PaymentInitializeView.as_view(), name='payment-initialize'),
  path('api/payments/verify/<str:reference>/', PaymentVerifyView.as_view(), name='payment-verify'),
  path('api/payments/history/', PaymentHistoryView.as_view(), name='payment-history'),

  ---
  Frontend Implementation

  1. Payment Service (src/services/paymentService.ts)

  export interface PaymentData {
    appointmentId?: number;
    amount: number;
    currency: string;
    appointmentType: string;
    departmentId?: number;
    hospitalId?: number;
    appointmentDate: string;
    symptoms?: any[];  // Will be mapped to symptoms_data
    chiefComplaint?: string;
    // ... other fields
  }

  export const PaymentService = {
    // Check payment system status
    async getPaymentStatus(): Promise<PaymentStatusResponse> {
      try {
        const response = await apiRequest<PaymentStatusResponse>(
          '/api/payments/status/',
          'GET'
        );
        return response;
      } catch (error: any) {
        // Return default enabled state on error
        return {
          payments_enabled: true,
          message: 'Unable to check payment status',
          available_providers: ['paystack'],
          free_appointments: false
        };
      }
    },

    // Initialize payment
    async initializePayment(paymentData: PaymentData): Promise<PaymentInitResponse> {
      try {
        const requestBody: any = {
          amount: paymentData.amount,
          payment_method: 'card',
          payment_provider: 'paystack'
        };

        // Payment-first approach: Send comprehensive booking details
        if (!paymentData.appointmentId) {
          requestBody.department_id = paymentData.departmentId;
          requestBody.hospital_id = paymentData.hospitalId;
          requestBody.appointment_date = paymentData.appointmentDate;

          // Handle symptoms_data correctly
          if (paymentData.symptoms && paymentData.symptoms.length > 0) {
            requestBody.symptoms_data = paymentData.symptoms.map((symptom: any) => ({
              body_part_id: symptom.bodyPartId,
              body_part_name: symptom.bodyPartName,
              symptom_name: symptom.symptomName,
              description: symptom.description || ''
            }));
          } else {
            // Always provide symptoms_data as empty array
            requestBody.symptoms_data = [];
          }
        }

        const response = await apiRequest('/api/payments/initialize/', 'POST', requestBody);

        // Handle payment disabled response
        if (response.payments_enabled === false || response.payment_status === 'waived') {
          return {
            status: 'success',
            data: {
              authorization_url: '',
              access_code: response.appointment_id || 'free-appointment',
              reference: 'waived-payment'
            },
            message: response.message || 'Appointment created successfully with waived payment',
            isPaymentWaived: true
          };
        }

        // Normal payment response
        return {
          status: 'success',
          data: {
            authorization_url: response.payment_url!,
            access_code: response.payment_id!,
            reference: response.provider_reference!
          }
        };
      } catch (error: any) {
        return {
          status: 'error',
          message: error.message || 'Payment initialization failed'
        };
      }
    }
  };

  2. BookAppointment Component (src/features/health/BookAppointment.tsx)

  const BookAppointment = () => {
    const [paymentStatus, setPaymentStatus] = useState<PaymentStatusResponse | null>(null);
    const [isPaymentWaived, setIsPaymentWaived] = useState(false);

    useEffect(() => {
      // Check payment status on component mount
      const checkPaymentStatus = async () => {
        try {
          const status = await PaymentService.getPaymentStatus();
          setPaymentStatus(status);
          setIsPaymentWaived(!status.payments_enabled);
        } catch (error) {
          console.error('Failed to check payment status:', error);
        }
      };

      checkPaymentStatus();
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();

      try {
        // Prepare payment data
        const paymentDataForModal = {
          amount: calculateAppointmentPrice(formData),
          currency: 'NGN',
          appointmentType: formData.appointmentType,
          departmentId: parseInt(formData.department),
          hospitalId: parseInt(formData.hospital),
          appointmentDate: formData.appointmentDateTime,
          symptoms: formData.selectedSymptoms,  // Will be mapped to symptoms_data
          chiefComplaint: formData.chiefComplaint,
          // ... other fields
        };

        // Initialize payment (works for both enabled/disabled modes)
        const paymentInitResult = await PaymentService.initializePayment(paymentDataForModal);

        if (paymentInitResult.status === 'success') {
          if (paymentInitResult.isPaymentWaived) {
            // Payment disabled - appointment created successfully
            setBookingSuccess(true);
            setSuccessMessage(paymentInitResult.message || 'Appointment booked successfully!');
          } else {
            // Payment enabled - show payment modal
            setShowPaymentModal(true);
            setPaymentData(paymentDataForModal);
            setPaymentReference(paymentInitResult.data.reference);
          }
        } else {
          throw new Error(paymentInitResult.message);
        }
      } catch (error: any) {
        setError(error.message || 'Failed to book appointment');
      }
    };

    return (
      <div className="book-appointment">
        {/* Payment status indicator */}
        {paymentStatus && (
          <div className={`payment-status ${isPaymentWaived ? 'free' : 'paid'}`}>
            {isPaymentWaived ? '🆓 Free Appointments Available' : '💳 Payment Required'}
          </div>
        )}

        {/* Booking form */}
        <form onSubmit={handleSubmit}>
          {/* Form fields... */}

          <button type="submit">
            {isPaymentWaived ? 'Book Free Appointment' : 'Proceed to Payment'}
          </button>
        </form>

        {/* Payment Modal (only shown when payments enabled) */}
        {showPaymentModal && !isPaymentWaived && (
          <PaymentModal
            isOpen={showPaymentModal}
            onClose={() => setShowPaymentModal(false)}
            paymentData={paymentData}
            paymentReference={paymentReference}
          />
        )}
      </div>
    );
  };

  3. Payment Modal Component (src/components/modals/PaymentModal.tsx)

  const PaymentModal: React.FC<PaymentModalProps> = ({ 
    isOpen, 
    onClose, 
    paymentData, 
    paymentReference 
  }) => {
    const [paymentStatus, setPaymentStatus] = useState<'pending' | 'success' | 'failed'>('pending');

    const handlePaymentSuccess = async (reference: string) => {
      try {
        // Verify payment with backend
        const verificationResult = await PaymentService.verifyPayment(reference);

        if (verificationResult.status === 'success') {
          setPaymentStatus('success');
          // Show success message and redirect
        } else {
          setPaymentStatus('failed');
        }
      } catch (error) {
        setPaymentStatus('failed');
      }
    };

    return (
      <Modal isOpen={isOpen} onClose={onClose}>
        <div className="payment-modal">
          <h2>Complete Your Payment</h2>

          <div className="payment-summary">
            <p>Amount: ₦{paymentData.amount}</p>
            <p>Department: {paymentData.department}</p>
            <p>Date: {paymentData.appointmentDate}</p>
          </div>

          {/* Paystack payment integration */}
          <PaystackButton
            reference={paymentReference}
            email={paymentData.patientEmail}
            amount={paymentData.amount * 100} // Paystack expects kobo
            publicKey={process.env.REACT_APP_PAYSTACK_PUBLIC_KEY}
            onSuccess={handlePaymentSuccess}
            onClose={onClose}
          />
        </div>
      </Modal>
    );
  };

  ---
  How to Enable Payments

  Backend Steps

  1. Update Environment Variables
  # .env file
  PAYMENTS_ENABLED=True
  PAYSTACK_SECRET_KEY=sk_live_your_live_secret_key
  PAYSTACK_PUBLIC_KEY=pk_live_your_live_public_key

  2. Configure Paystack Settings
  # server/settings.py
  PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
  PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY')

  # For production, use live keys
  PAYMENT_PROVIDERS = {
      'paystack': {
          'secret_key': PAYSTACK_SECRET_KEY,
          'public_key': PAYSTACK_PUBLIC_KEY,
          'base_url': 'https://api.paystack.co',
      }
  }

  3. Test Payment Integration
  # Add to your test suite
  def test_payment_enabled_flow():
      with self.settings(PAYMENTS_ENABLED=True):
          response = self.client.post('/api/payments/initialize/', payment_data)
          self.assertEqual(response.status_code, 200)
          self.assertIn('payment_url', response.data)

  Frontend Steps

  1. Update Environment Variables
  # .env or .env.production
  REACT_APP_PAYSTACK_PUBLIC_KEY=pk_live_your_live_public_key
  VITE_API_BASE_URL=https://your-backend-domain.com

  2. Install Required Dependencies
  npm install react-paystack

  3. Update Payment Service Configuration
  // src/config/payment.ts
  export const PAYMENT_CONFIG = {
    providers: {
      paystack: {
        publicKey: import.meta.env.VITE_PAYSTACK_PUBLIC_KEY,
        apiUrl: 'https://api.paystack.co'
      }
    },
    defaultProvider: 'paystack',
    currency: 'NGN'
  };

  4. Build and Deploy
  npm run build
  # Deploy dist folder to your hosting service

  Production Deployment Checklist

  Backend

  - Set PAYMENTS_ENABLED=True
  - Use live Paystack keys (sk_live_*, pk_live_*)
  - Configure webhook endpoints for payment notifications
  - Set up SSL certificates for secure payment processing
  - Configure CORS for frontend domain
  - Set up monitoring for payment failures
  - Configure backup payment provider (optional)

  Frontend

  - Use production Paystack public key
  - Point API calls to production backend URL
  - Enable production build optimizations
  - Configure CDN for static assets
  - Set up error tracking (Sentry, LogRocket, etc.)
  - Test payment flow in staging environment
  - Configure analytics tracking for payment events

  Testing

  - Test with Paystack test cards
  - Verify payment verification webhook
  - Test appointment creation after successful payment
  - Test payment failure scenarios
  - Test appointment cancellation and refunds
  - Load test payment system under high traffic

  ---
  Payment Flow Diagrams

  Payment Disabled Flow

  User fills form → Frontend calls PaymentService.initializePayment()
  → Backend checks PAYMENTS_ENABLED=False → Backend creates appointment directly 
  → Backend sets payment_status='waived' → Success response to frontend
  → User sees "Appointment booked successfully!"

  Payment Enabled Flow

  User fills form → Frontend calls PaymentService.initializePayment()
  → Backend checks PAYMENTS_ENABLED=True → Backend creates PaymentTransaction 
  → Backend returns Paystack payment URL → Frontend shows PaymentModal 
  → User completes payment on Paystack → Frontend verifies payment 
  → Backend creates appointment → Success confirmation

  ---
  Troubleshooting

  Common Issues

  1. "symptoms_data cannot be blank" Error
    - Cause: Frontend sending empty string instead of empty array
    - Solution: Ensure symptoms_data: [] is sent in requests
  2. "NoneType object has no attribute 'user'" Error
    - Cause: Notification system accessing unassigned doctor
    - Solution: Check doctor exists before accessing doctor.user
  3. Payment verification fails
    - Cause: Webhook signature validation or network issues
    - Solution: Check Paystack webhook configuration and logs
  4. Frontend payment modal not showing
    - Cause: Payment status not properly checked
    - Solution: Verify PaymentService.getPaymentStatus() is called

  Debug Tools

  1. Backend Logging
  # Add to payment views for debugging
  logger.debug(f"Payment request data: {request.data}")
  logger.debug(f"Payment status: {getattr(settings, 'PAYMENTS_ENABLED', True)}")

  2. Frontend Debug Console
  // Add to PaymentService for debugging
  console.log('🔍 Payment status:', paymentStatus);
  console.log('💰 Payment data:', paymentData);

  3. Database Inspection
  -- Check appointment payment status
  SELECT appointment_id, payment_status, payment_required, created_at
  FROM api_appointment
  ORDER BY created_at DESC LIMIT 10;

  -- Check payment transactions
  SELECT payment_id, status, amount, created_at
  FROM api_paymenttransaction
  ORDER BY created_at DESC LIMIT 10;

  This documentation provides a complete guide for understanding and managing the payment system. The architecture supports seamless switching between free
  and paid modes, making it flexible for different deployment scenarios.