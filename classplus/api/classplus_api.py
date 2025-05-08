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

        student_name = data.get("student_name")
        student_mobile = data.get("student_mobile")
        course_name = data.get("course_name")
        course_price = data.get("course_price")
        current_time = frappe.utils.now()

        if not student_mobile or not course_name or not course_price:
            return {"status": "error", "message": "Missing required fields"}

        existing_lead = frappe.get_list("Lead", filters={"mobile_no": student_mobile}, limit=1)

        # If lead exists, update course price
        if existing_lead:
            lead = frappe.get_doc("Lead", existing_lead[0].name)

            course_exists = False
            for course in lead.get("course", []):
                if course.course_name == course_name:
                    # Update existing course entry
                    course.price = course_price
                    course_exists = True
                    break
            
            if not course_exists:
                # Append new course entry
                lead.append("course", {
                    "course_name": course_name,
                    "price": course_price,
                    "time": current_time
                })

            lead.event_ = "Bought Course"
                
            lead.save(ignore_permissions=True)
            frappe.db.commit()
            return {"status": "success", "message": "Course updated" if course_exists else "New course added to existing student"}
        
        # If lead doesn't exist, create a new one
        else:
            new_lead = frappe.get_doc({
                "doctype": "Lead",
                "first_name": student_name,
                "mobile_no": student_mobile,
                "source": "Classplus",
                "event_": "Bought Course",
                "course": [{
                    "course_name": course_name,
                    "price": course_price,
                    "time": current_time
                }]
            })
            
            new_lead.insert(ignore_permissions=True)
            frappe.db.commit()
            return {"status": "success", "message": "New lead created with course"}

    except Exception as e:
        frappe.logger().error(f"Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}
