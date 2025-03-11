import frappe
import requests

@frappe.whitelist()
def fetch_classplus_data():
    api_url = "http://data.classplus.co/api/queries/15496/results.json?api_key=fHyqfEEWi8SOCaAL4G0cYArrCiik7GrdmSuoHk0e"
    
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not ("query_result" in data and "data" in data["query_result"]):
            return {"error": "Invalid API response format"}
            
        records = data["query_result"]["data"].get("rows", [])
        if not records:
            return {"message": "No records found"}
        
        mobile_to_record = {}
        for record in records:
            mobile = record.get("mobile")
            if mobile: 
                mobile_to_record[mobile] = record
        
        if not mobile_to_record:
            return {"message": "No valid records with mobile numbers found"}
        
        all_mobiles = list(mobile_to_record.keys())

        existing_records = frappe.get_all(
            "Student Classplus",
            filters={"student_mobile": ["in", all_mobiles]},
            fields=["name", "student_mobile"]
        )
        
        existing_mobiles_dict = {record.student_mobile: record.name for record in existing_records}

        new_count = 0
        update_count = 0

        docs_to_save = []
        
        for mobile, record in mobile_to_record.items():
            if mobile in existing_mobiles_dict:
                student_doc = frappe.get_doc("Student Classplus", existing_mobiles_dict[mobile])
                update_count += 1
            else:
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

        if hasattr(frappe, 'bulk_save'):  
            frappe.bulk_save(docs_to_save, ignore_permissions=True)
        else:
            for doc in docs_to_save:
                doc.save(ignore_permissions=True)
        
        total_processed = new_count + update_count
        return {
            "message": f"Processed {total_processed} records successfully",
            "new_entries": new_count,
            "updated_entries": update_count
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}