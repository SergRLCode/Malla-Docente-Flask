from routes.authLogin import *
    # JWT middleware
    # /login
    # /logout
from routes.courses import *
    # /courses
    # /periods
    # /coursesByPeriod/<period>
    # /availableCourses
    # /course/<name>
    # /editSerial/<course>
from routes.course_requests import *
    # /addTeacherinCourse/<course_name>
    # /rejectTeacherOfCourse/<name>
    # /courseRequest/<name>
    # /requestsTo/<name>
    # /getRequests
    # /cancelRequest/<course>
from routes.metadataPDFS import *
    # /metadata
    # /metadata/<doc>
from routes.routes_pdfs import *
    # /courses/coursesList
    # /course/<name>/assistantList
    # /inscriptionDocument/<name>
    # /establishLimitDaysOfPoll
    # /course/<name>/poll
    # /dataConcentrated
from routes.teachers import *
    # /teachers
    # /teacher/<rfc>
    # /teachersByDep/<course>
    # /changePassword
from routes.teacher_course import *
    # /myCourses
    # /myCoursesWillTeach
    # /coursesOf/<rfc>
    # /teacherList/<course>
    # /removeTeacherinCourse/<name>
    # /teacherListToQualify/<course>
    # /approvedCourse/<name>
    # /failedCourse/<name>
from routes.notFound import *
    # special route for 404