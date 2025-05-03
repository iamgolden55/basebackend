import uuid
from datetime import datetime, timedelta
from icalendar import Calendar, Event, vText
import pytz

def generate_ics_for_appointment(appointment):
    """
    Generate an iCalendar (.ics) file for an appointment
    
    Args:
        appointment: The appointment object with all booking details
    
    Returns:
        bytes: The iCalendar file contents as bytes
    """
    # Create calendar
    cal = Calendar()
    cal.add('prodid', '-//PHB Medical Appointment System//mxm.dk//')
    cal.add('version', '2.0')
    
    # Create event
    event = Event()
    
    # Add basic event metadata
    event_uid = f'appointment-{appointment.appointment_id}@phb.com'
    event.add('uid', event_uid)
    event.add('dtstamp', datetime.now(tz=pytz.UTC))
    
    # Set event start and end times
    start_time = appointment.appointment_date
    end_time = start_time + timedelta(minutes=appointment.duration)
    
    event.add('dtstart', start_time)
    event.add('dtend', end_time)
    
    # Add event details
    doctor_name = appointment.doctor.full_name
    hospital_name = appointment.hospital.name
    department_name = appointment.department.name
    
    summary = f"Medical Appointment with Dr. {doctor_name}"
    event.add('summary', summary)
    
    # Generate a detailed description
    description = (
        f"Appointment ID: {appointment.appointment_id}\n"
        f"Doctor: {doctor_name}\n"
        f"Department: {department_name}\n"
        f"Hospital: {hospital_name}\n"
        f"Type: {dict(appointment.APPOINTMENT_TYPE_CHOICES).get(appointment.appointment_type, appointment.appointment_type)}\n"
        f"Priority: {dict(appointment.PRIORITY_CHOICES).get(appointment.priority, appointment.priority)}\n"
    )
    
    if appointment.chief_complaint:
        description += f"Chief Complaint: {appointment.chief_complaint}\n"
        
    event.add('description', description)
    
    # Add location
    location = f"{hospital_name} - {department_name} Department"
    event.add('location', location)
    
    # Set reminders (alarms) - 1 day and 1 hour before
    alarm1 = create_calendar_alarm(timedelta(days=1))
    alarm2 = create_calendar_alarm(timedelta(hours=1))
    event.add_component(alarm1)
    event.add_component(alarm2)
    
    # Add the event to the calendar
    cal.add_component(event)
    
    # Return the calendar as bytes
    return cal.to_ical()

def create_calendar_alarm(trigger_time):
    """Create a calendar alarm component"""
    from icalendar import Alarm
    
    alarm = Alarm()
    alarm.add('action', 'DISPLAY')
    alarm.add('description', 'Reminder')
    alarm.add('trigger', -trigger_time)
    
    return alarm 