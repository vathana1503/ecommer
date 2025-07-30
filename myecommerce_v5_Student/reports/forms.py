from django import forms
from django.utils import timezone
from datetime import timedelta


class ReportFilterForm(forms.Form):
    """
    Form for filtering sales reports by date range and type
    """
    REPORT_TYPE_CHOICES = [
        ('daily', 'Daily Report'),
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('yearly', 'Yearly Report'),
        ('custom', 'Custom Date Range'),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPE_CHOICES,
        initial='monthly',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    start_date = forms.DateField(
        initial=lambda: timezone.now().date() - timedelta(days=30),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    end_date = forms.DateField(
        initial=timezone.now().date,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError("Start date cannot be after end date.")
            
            if end_date > timezone.now().date():
                raise forms.ValidationError("End date cannot be in the future.")
        
        return cleaned_data


class ExportReportForm(forms.Form):
    """
    Form for exporting reports
    """
    FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('pdf', 'PDF'),
    ]
    
    export_format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        initial='csv',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    include_details = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Include detailed breakdown in the export"
    )
