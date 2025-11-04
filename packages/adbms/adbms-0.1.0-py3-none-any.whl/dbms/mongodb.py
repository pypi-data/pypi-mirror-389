def mongodb():
    """Returns MongoDB practice commands"""
    return """
# MongoDB Practice Commands

1️⃣ Update Raj’s grade and add new subject
db.students.updateOne(
  { name: "Raj" },
  { 
    $set: { grade: "B+" },
    $push: { subjects: "Computer Science" }
  }
)
db.students.find({ name: "Raj" }).pretty()

2️⃣ Delete Radha
db.students.deleteOne({ name: "Radha" })
db.students.find().pretty()

3️⃣ Comparison operator: Age >= 18
db.students.find({ age: { $gte: 18 } })

4️⃣ $in operator: Math or History
db.students.find({ subjects: { $in: ["Math", "History"] } })

5️⃣ $all operator: both Math and English
db.students.find({ subjects: { $all: ["Math", "English"] } })

6️⃣ Projection (only show name, subjects)
db.students.find({}, { name: 1, subjects: 1, _id: 0 })

7️⃣ Sorting + Limit
db.students.find().sort({ age: -1 }).limit(2)

8️⃣ Aggregation (group by grade and count)
db.students.aggregate([
  { $group: { _id: "$grade", total: { $sum: 1 } } }
])

9️⃣ Insert document with birthDate
db.students.insertOne({
  name: "Kiran",
  age: 19,
  grade: "A",
  subjects: ["Science"],
  birthDate: new Date("2006-04-15")
})
db.students.find({ birthDate: { $gt: new Date("2005-01-01") } })

🔟 Simple Lookup (teacher teaches student)
db.teachers.insertMany([
  { _id: 1, name: "Mr. Smith", subject: "Math" },
  { _id: 2, name: "Ms. Johnson", subject: "English" }
])
db.students.aggregate([
  {
    $lookup: {
      from: "teachers",
      localField: "subjects",
      foreignField: "subject",
      as: "teacherInfo"
    }
  }
])
"""
