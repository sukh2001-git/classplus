import frappe
import requests

@frappe.whitelist()
def fetch_classplus_data():
    api_url = "http://data.classplus.co/api/queries/15496/results.json?api_key=fHyqfEEWi8SOCaAL4G0cYArrCiik7GrdmSuoHk0e"
    
    try:
        # Fetch data from API
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Validate response structure
        if not ("query_result" in data and "data" in data["query_result"]):
            return {"error": "Invalid API response format"}
            
        records = data["query_result"]["data"].get("rows", [])
        if not records:
            return {"message": "No records found"}
        
        # Filter records with mobile numbers
        mobile_to_record = {}
        for record in records:
            mobile = record.get("mobile")
            if mobile: 
                mobile_to_record[mobile] = record
        
        if not mobile_to_record:
            return {"message": "No valid records with mobile numbers found"}
        
        all_mobiles = list(mobile_to_record.keys())

        # Get existing records
        existing_records = frappe.get_all(
            "Student Classplus",
            filters={"student_mobile": ["in", all_mobiles]},
            fields=["name", "student_mobile"]
        )
        
        existing_mobiles_dict = {record.student_mobile: record.name for record in existing_records}

        # Initialize counters
        new_count = 0
        skipped_count = 0
        docs_to_save = []
        
        # Process records
        for mobile, record in mobile_to_record.items():
            # Skip existing records
            if mobile in existing_mobiles_dict:
                skipped_count += 1
                continue
                
            # Create new records only
            student_doc = frappe.new_doc("Student Classplus")
            new_count += 1

            student_doc.update({
                "last_paid_date": record.get("lastPaidDate"),
                "total_number_of_installments": record.get("numberofinstallments"),
                "student_name": record.get("name"),
                "student_mobile": record.get("mobile"),
                "user_id": record.get("userid"),
                "paid_installments": record.get("PaidInstallments"),
                "expiry_date": record.get("ExpiryDate"),
                "course_id": record.get("courseid"),
                "enrollment_date": record.get("EnrollmentDate"),
                "course_name": record.get("CourseName"),
                "next_due_date": record.get("NextDueDate"),
                "is_active": record.get("isactive"),
                "total_installments_amount": record.get("TotalInstallmentsAmount"),
                "course_amount": record.get("courseAmount"),
                "total_installment_amount_paid": record.get("Total_InstallmentAmount_Paid"),
                "installment_amount_remaining": record.get("InstallmentAmountRemanining"),
                "unpaid_installments": record.get("UnpaidInstallments"),
            })
            
            docs_to_save.append(student_doc)

        # Save all new documents
        if docs_to_save:
            if hasattr(frappe, 'bulk_save'):  
                frappe.bulk_save(docs_to_save, ignore_permissions=True)
            else:
                for doc in docs_to_save:
                    doc.save(ignore_permissions=True)
        
        # Return results with counts
        return {
            "message": f"Process completed successfully",
            "new_entries": new_count,
            "skipped_entries": skipped_count,
            "total_processed": new_count + skipped_count
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
    


@frappe.whitelist()
def handle_pricing_data():
    try:
        data = frappe.request.json
        frappe.log_error("Data:", data)
        student_mobile = data.get("student_mobile")
        course_name = data.get("course_name")
        course_price = data.get("course_price")

        if not student_mobile or not course_name or not course_price:
            return {"status": "error", "message": "Missing required fields"}

        existing_lead = frappe.get_list("Lead", filters={"mobile_no": student_mobile}, limit=1)

        if existing_lead:
            lead = frappe.get_doc("Lead", existing_lead[0].name)

            for course in lead.get("course"):
                if course.course_name == course_name:
                    course.price = course_price
                    lead.save(ignore_permissions=True)
                    frappe.db.commit()
                    return {"status": "success", "message": "Course price updated"}

        return {"status": "error", "message": "Lead or course not found"}

    except Exception as e:
        frappe.logger().error(f"Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}
