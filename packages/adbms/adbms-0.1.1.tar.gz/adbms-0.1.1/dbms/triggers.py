def triggers():
    """Returns Oracle Trigger Practicals"""
    return """
--------------------------
1️⃣ Insert new employee → update total hours
--------------------------
CREATE OR REPLACE TRIGGER trg_emp_insert
AFTER INSERT ON emp
FOR EACH ROW
BEGIN
  UPDATE project SET thrs = thrs + :NEW.hrs WHERE pno = :NEW.pno;
END;
/

--------------------------
2️⃣ Update employee hrs → adjust total
--------------------------
CREATE OR REPLACE TRIGGER trg_emp_update_hrs
AFTER UPDATE OF hrs ON emp
FOR EACH ROW
BEGIN
  UPDATE project SET thrs = thrs - :OLD.hrs + :NEW.hrs WHERE pno = :NEW.pno;
END;
/

--------------------------
3️⃣ Change employee project
--------------------------
CREATE OR REPLACE TRIGGER trg_emp_change_project
AFTER UPDATE OF pno ON emp
FOR EACH ROW
BEGIN
  UPDATE project SET thrs = thrs - :OLD.hrs WHERE pno = :OLD.pno;
  UPDATE project SET thrs = thrs + :NEW.hrs WHERE pno = :NEW.pno;
END;
/

--------------------------
4️⃣ Delete employee → reduce project hours
--------------------------
CREATE OR REPLACE TRIGGER trg_emp_delete
AFTER DELETE ON emp
FOR EACH ROW
BEGIN
  UPDATE project SET thrs = thrs - :OLD.hrs WHERE pno = :OLD.pno;
END;
/

--------------------------
5️⃣ Log all actions (insert/update/delete)
--------------------------
CREATE TABLE emp_log(log_date DATE, action VARCHAR2(20));

CREATE OR REPLACE TRIGGER trg_emp_log
AFTER INSERT OR UPDATE OR DELETE ON emp
BEGIN
  IF INSERTING THEN
    INSERT INTO emp_log VALUES (SYSDATE, 'INSERT');
  ELSIF UPDATING THEN
    INSERT INTO emp_log VALUES (SYSDATE, 'UPDATE');
  ELSIF DELETING THEN
    INSERT INTO emp_log VALUES (SYSDATE, 'DELETE');
  END IF;
END;
/

--------------------------
6️⃣ Set pno NULL when project deleted
--------------------------
CREATE OR REPLACE TRIGGER trg_project_delete
AFTER DELETE ON project
FOR EACH ROW
BEGIN
  UPDATE emp SET pno = NULL WHERE pno = :OLD.pno;
END;
/

--------------------------
7️⃣ Prevent update on Sunday
--------------------------
CREATE OR REPLACE TRIGGER trg_no_update_sunday
BEFORE UPDATE ON emp
BEGIN
  IF TO_CHAR(SYSDATE, 'DY') = 'SUN' THEN
    RAISE_APPLICATION_ERROR(-20001, 'Updates not allowed on Sunday!');
  END IF;
END;
/

--------------------------
8️⃣ Log deletion in EMPCHGLOG
--------------------------
CREATE TABLE EMPCHGLOG(change_date DATE, action VARCHAR2(20), pno NUMBER);

CREATE OR REPLACE TRIGGER trg_emp_delete_log
AFTER DELETE ON emp
FOR EACH ROW
BEGIN
  INSERT INTO EMPCHGLOG VALUES (SYSDATE, 'Employee deleted', :OLD.pno);
END;
/

--------------------------
9️⃣ Copy student record from stud1 → stud2
--------------------------
CREATE OR REPLACE TRIGGER trg_copy_student
AFTER INSERT ON stud1
FOR EACH ROW
BEGIN
  INSERT INTO stud2 VALUES(:NEW.roll_no, :NEW.firstname, :NEW.lastname);
END;
/

--------------------------
🔟 Calculate commission in salesmanager
--------------------------
CREATE OR REPLACE TRIGGER trg_sales_comm
BEFORE INSERT OR UPDATE ON salesmanager
FOR EACH ROW
BEGIN
  IF :NEW.salary < 10000 THEN
    :NEW.comm := :NEW.salary * 0.03;
  ELSIF :NEW.salary < 30000 THEN
    :NEW.comm := :NEW.salary * 0.05;
  ELSE
    :NEW.comm := :NEW.salary * 0.07;
  END IF;
END;
/

--------------------------
11️⃣ Auto-generate bookid
--------------------------
CREATE SEQUENCE book_seq START WITH 1 INCREMENT BY 1;

CREATE OR REPLACE TRIGGER trg_bookid_auto
BEFORE INSERT ON books
FOR EACH ROW
BEGIN
  SELECT book_seq.NEXTVAL INTO :NEW.bookid FROM dual;
END;
/

--------------------------
12️⃣ Ensure product unit_price > 0
--------------------------
CREATE OR REPLACE TRIGGER trg_check_price
BEFORE INSERT OR UPDATE ON product
FOR EACH ROW
BEGIN
  IF :NEW.unit_price <= 0 THEN
    RAISE_APPLICATION_ERROR(-20002, 'Unit price must be greater than 0');
  END IF;
END;
/
"""
